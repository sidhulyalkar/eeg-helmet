"""Numerical qualification of the S0 reduced-order simulator.

This reports *discretization sensitivity*, not a physical validation, NOCSAE
qualification, concussion outcome or commercial-helmet comparison.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite
from .models import Parameters, SCENARIOS
from .physics import simulate
from .provenance import canonical_hash

OBSERVABLES = (
    "peak_head_accel_g",
    "peak_angular_accel_rad_s2",
    "peak_head_angular_speed_rad_s",
    "peak_neck_torque_proxy_nm",
    "peak_mount_deflection_mm",
)
DT_LEVELS_S = (0.001, 0.0005, 0.00025, 0.000125)


def _fractional_change(a: float, b: float) -> float:
    # No near-zero denominator masking. A quantity indistinguishable from zero
    # is a separate indeterminate observation, not zero relative error.
    if max(abs(a), abs(b)) < 1e-8:
        return 0.0
    if abs(b) < 1e-8:
        return float("inf")
    return abs(a-b) / abs(b)


def qualify(scenario: str, params: Parameters | None = None,
            tolerance: float = 0.05) -> dict:
    """Compare four step sizes and report changes between the two finest.

    A PASS is always numerical_step_refinement only. Stiff stop engagement
    and unknown analytical error are retained as explicit limitations.
    """
    if scenario not in SCENARIOS:
        raise ValueError("Unknown scenario")
    if isinstance(tolerance, bool) or not isinstance(tolerance, (float, int)) or not isfinite(tolerance) or not 0 < tolerance <= 0.25:
        raise ValueError("tolerance must be finite within (0, 0.25]")
    p = params or Parameters()
    runs = [simulate(scenario, p, dt=dt) for dt in DT_LEVELS_S]
    rows = []
    for key in OBSERVABLES:
        observed = [r["metrics"][key] for r in runs]
        last_change = _fractional_change(observed[-2], observed[-1])
        previous_change = _fractional_change(observed[-3], observed[-2])
        rows.append({"metric": key, "values": observed,
                     "coarse_to_medium_change": round(previous_change, 7),
                     "medium_to_fine_change": round(last_change, 7),
                     "within_tolerance": last_change <= tolerance})
    all_stops = [r["metrics"]["mount_limit_engaged"] for r in runs]
    result = {
        "schema_version": "0.2.0",
        "source": "SYNTHETIC_NUMERICAL_STEP_REFINEMENT",
        "evidence_level": "S0_UNVALIDATED_MECHANICS",
        "scenario": scenario,
        "parameters": p.to_dict(),
        "step_sizes_s": DT_LEVELS_S,
        "comparison": "relative change of each rounded peak value between the finest two step sizes",
        "tolerance_fraction": tolerance,
        "metrics": rows,
        "mount_stop_engaged": all_stops,
        "status": "PASS_NUMERICAL_REFINEMENT_ONLY" if all(r["within_tolerance"] for r in rows) else "FAIL_NUMERICAL_REFINEMENT",
        "limitations": ["No independent integrator or analytical reference solution",
                        "No measured helmet or instrumented headform data",
                        "Peak metrics rounded by the toy simulator before comparison",
                        "No tissue-strain, injury-risk or clinical inference"],
    }
    result["report_sha256"] = canonical_hash(result)
    return result
