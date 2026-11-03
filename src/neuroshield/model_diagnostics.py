"""S0-only local sensitivity diagnostics for the illustrative three-body simulator.

This is *model-form exploration*, not parameter identification from observations,
physics calibration, Bayesian inference, or helmet safety evaluation. No data access.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import replace
from pathlib import Path

from .models import Parameters, SCENARIOS
from .physics import simulate
from .provenance import canonical_hash

SCHEMA = "neuroshield.model-sensitivity/0.1"
PARAMETERS = tuple(Parameters.__dataclass_fields__)
METRICS = (
    "peak_head_accel_g",
    "peak_angular_accel_rad_s2",
    "peak_head_angular_speed_rad_s",
    "peak_neck_torque_proxy_nm",
    "peak_mount_deflection_mm",
)
# A scalar or proxy is not a vector resultant, a neck load cell, or a validation.
METRIC_INTERPRETATION = {
    "peak_head_accel_g": "1D model head acceleration magnitude, NOT 3D instrument resultant",
    "peak_angular_accel_rad_s2": "1D rotational-axis model peak, NOT 3D headform angular resultant",
    "peak_head_angular_speed_rad_s": "1D rotational-axis model peak, NOT 3D headform angular speed resultant",
    "peak_neck_torque_proxy_nm": "fixed-torso spring/damper reaction PROXY, NOT instrumented upper-neck moment",
    "peak_mount_deflection_mm": "scalar facemask-to-shell relative displacement, NOT tested device clearance",
}
HALF_STEP = .005
FULL_STEP = .01
LOW_ELASTICITY_RMS = .01
NEAR_COLLINEAR_COS = .98
DERIVATIVE_CHANGE_FRACTION = .25
ZERO_PEAK = 1e-9


def _params(preset: str) -> Parameters:
    if preset == "default":
        return Parameters()
    if preset == "suggested":
        return Parameters.suggested()
    raise ValueError("Unknown fixed parameter preset")


def _scenarios(name: str) -> list[str]:
    if name == "all":
        return list(SCENARIOS)
    if not isinstance(name, str) or name not in SCENARIOS:
        raise ValueError("Unknown allowlisted synthetic impact scenario")
    return [name]


def _run(scene: str, p: Parameters) -> dict:
    run = simulate(scene, p)
    peaks = run["metrics_unrounded"]
    if set(METRICS) - set(peaks):
        raise ValueError("Scientific observable contract changed")
    if any(type(peaks[key]) not in (int, float) or not math.isfinite(peaks[key])
           or peaks[key] < 0 for key in METRICS):
        raise ArithmeticError("Nonfinite or negative absolute peak from synthetic solver")
    return run


def _central(scene: str, params: Parameters, name: str, fraction: float):
    value = getattr(params, name)
    if not isinstance(value, (float, int)) or value <= 0:
        raise ValueError("Only strictly positive physical model parameters supported")
    plus = replace(params, **{name: value*(1 + fraction)})
    minus = replace(params, **{name: value*(1 - fraction)})
    # The same bounds as published simulation inputs, no hidden extrapolation.
    Parameters.from_payload(plus.to_dict())
    Parameters.from_payload(minus.to_dict())
    a = _run(scene, plus)
    b = _run(scene, minus)
    return a, b


def _cosine(a: list[float], b: list[float]) -> float | None:
    if len(a) != len(b) or not a:
        return None
    na = math.sqrt(sum(v*v for v in a))
    nb = math.sqrt(sum(v*v for v in b))
    if na < 1e-10 or nb < 1e-10:
        return None
    result = sum(x*y for x,y in zip(a,b)) / (na*nb)
    return max(-1., min(1., result))


def evaluate(*, scenario: str = "all", preset: str = "default") -> dict:
    """Compare central finite differences at 1% and .5% on synthetic peak responses.

    Structural and numerical local sensitivity is *not* practical identifiability:
    measurement noise, population variability, model discrepancy and calibration
    are not represented.
    """
    scenarios = _scenarios(scenario)
    params = _params(preset)
    samples, rows = [], []
    warnings = set()
    for scene in scenarios:
        base = _run(scene, params)
        base_peaks = base["metrics_unrounded"]
        samples.append({
            "scenario": scene,
            "scientific_fingerprint": base["provenance"]["scientific_fingerprint"],
            "mount_limit_engaged": base["metrics"]["mount_limit_engaged"],
        })
        derivatives = {}
        for name in PARAMETERS:
            a, b = _central(scene, params, name, FULL_STEP)
            small_a, small_b = _central(scene, params, name, HALF_STEP)
            derivatives[name] = {
                "large": {key: (a["metrics_unrounded"][key] - b["metrics_unrounded"][key])/(2*FULL_STEP)
                          for key in METRICS},
                "small": {key: (small_a["metrics_unrounded"][key] - small_b["metrics_unrounded"][key])/(2*HALF_STEP)
                          for key in METRICS},
            }
            flags = {base["metrics"]["mount_limit_engaged"], a["metrics"]["mount_limit_engaged"],
                     b["metrics"]["mount_limit_engaged"], small_a["metrics"]["mount_limit_engaged"],
                     small_b["metrics"]["mount_limit_engaged"]}
            if len(flags) > 1:
                warnings.add("LIMIT_STOP_SWITCHING_UNDER_PERTURBATION")
        for metric in METRICS:
            reference = base_peaks[metric]
            entries = {}
            for name in PARAMETERS:
                big = derivatives[name]["large"][metric]
                small = derivatives[name]["small"][metric]
                if not math.isfinite(big) or not math.isfinite(small):
                    raise ArithmeticError("Nonfinite local sensitivity")
                scale = max(abs(big), abs(small))
                fraction = (abs(big - small)/scale) if scale > 1e-9 else 0.
                unstable = fraction > DERIVATIVE_CHANGE_FRACTION and scale > 1e-6
                if unstable:
                    warnings.add("LOCAL_PEAK_DERIVATIVE_DEPENDS_ON_STEP")
                elasticity = small/reference if reference >= ZERO_PEAK else None
                if elasticity is not None and not math.isfinite(elasticity):
                    raise ArithmeticError("Nonfinite normalized sensitivity")
                entries[name] = {
                    "percent_parameter_elasticity": elasticity,
                    "absolute_metric_change_per_unit_parameter_fraction": small,
                    "fractional_derivative_step_difference": fraction,
                    "derivative_stability_warning": unstable,
                }
            if reference < ZERO_PEAK:
                warnings.add("ZERO_BASELINE_METRIC_CANNOT_BE_NORMALIZED")
            rows.append({
                "scenario": scene,
                "metric": metric,
                "metric_context": METRIC_INTERPRETATION[metric],
                "baseline_absolute_peak": reference,
                "directly_comparable_to_physical_3d_measurement": False,
                "sensitivities": entries,
            })
    columns = {p: [row["sensitivities"][p]["percent_parameter_elasticity"]
                   for row in rows] for p in PARAMETERS}
    pairs = []
    for index, first in enumerate(PARAMETERS):
        for second in PARAMETERS[index+1:]:
            values = [(x,y) for x,y in zip(columns[first], columns[second])
                      if x is not None and y is not None]
            similarity = _cosine([x for x,_ in values],[y for _,y in values]) if len(values) >= 3 else None
            flag = similarity is not None and abs(similarity) >= NEAR_COLLINEAR_COS
            if flag:
                warnings.add("SIMILAR_PARAMETER_SENSITIVITY_PATTERNS")
            pairs.append({"parameters": [first, second], "cosine": similarity,
                          "overlapping_nonzero_metrics": len(values),
                          "similar_patterns_heuristic": flag})
    parameter_rms = {}
    for name in PARAMETERS:
        values = [v for v in columns[name] if v is not None]
        rms = math.sqrt(sum(x*x for x in values)/len(values)) if values else None
        parameter_rms[name] = rms
        if rms is None or rms < LOW_ELASTICITY_RMS:
            warnings.add("PARAMETER_HAS_LOW_LOCAL_PEAK_SENSITIVITY")
    report = {
        "schema_version": SCHEMA,
        "status": "SYNTHETIC_LOCAL_SENSITIVITY_ONLY",
        "scientific_evidence_level": "S0",
        "source": "deterministic_unvalidated_three_body_simulator",
        "scenario_angle_deg_is_dynamical_input": False,
        "preset": preset, "scenarios": scenarios, "parameters": params.to_dict(),
        "model_source_bound_run_fingerprints": samples,
        "analyzed_metrics": list(METRICS),
        "model_observable_rows": rows,
        "parameter_pair_pattern_cosines": pairs,
        "parameter_rms_elasticity": parameter_rms,
        "heuristic_thresholds": {
            "relative_perturbations": [HALF_STEP, FULL_STEP],
            "local_derivative_step_change": DERIVATIVE_CHANGE_FRACTION,
            "low_parameter_rms_elasticity": LOW_ELASTICITY_RMS,
            "similar_parameter_patterns_abs_cosine": NEAR_COLLINEAR_COS,
        },
        "warnings": sorted({*warnings, "SCENARIO_ANGLE_METADATA_NOT_FORCE_DIRECTION"}),
        "measured_data_analyzed": False,
        "physical_parameters_identified": False,
        "calibration_verified": False,
        "physical_model_validation": False,
        "safety_or_injury_inference_permitted": False,
        "interpretation": "Local finite-difference behavior of simulated peak functions only. A similar cosine is not a statistical identifiability test. Peak maxima can change branch or activate travel stops. No 3D measurement operator, instrument uncertainty, physical calibration, helmet approval or medical inference.",
    }
    report["report_sha256"] = canonical_hash(report)
    return report


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Offline S0 synthetic model-form sensitivity audit")
    p.add_argument("--scenario", default="all", choices=["all", *SCENARIOS])
    p.add_argument("--preset", default="default", choices=["default", "suggested"])
    p.add_argument("--out", type=Path)
    args = p.parse_args(argv)
    try:
        report = evaluate(scenario=args.scenario, preset=args.preset)
        serialized = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
        if args.out is None:
            print(serialized, end="")
        else:
            if args.out.exists() or args.out.is_symlink():
                raise ValueError("Output must be a new file; existing files are never replaced")
            with args.out.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(serialized)
    except (ValueError, OSError, ArithmeticError) as exc:
        p.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
