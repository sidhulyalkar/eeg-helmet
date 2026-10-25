"""Preregistered, local-only headform waveform comparisons.

A numerical / descriptive *screen*, not a concussion or helmet-safety model.
Never aligns traces by optimizing their difference and never exports raw samples.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from .bench_intake import _iter_samples, _read_profile, _norm3, validate_intake
from .headform import _metadata
from .provenance import canonical_hash

COMPONENTS = {
    "linear_acceleration_m_s2": (1, 4, "linear_acceleration_m_s2"),
    "angular_acceleration_rad_s2": (4, 7, "angular_acceleration_rad_s2"),
    "angular_velocity_rad_s": (7, 10, "angular_velocity_rad_s"),
}
MAX_PLAN_BYTES = 16_384


def _finite_number(v, name, *, min_value=None, max_value=None):
    if type(v) not in (int, float) or not math.isfinite(v):
        raise ValueError(f"{name}: expected finite number")
    v = float(v)
    if min_value is not None and v < min_value or max_value is not None and v > max_value:
        raise ValueError(f"{name}: outside supported range")
    return v


def read_plan(path):
    p = Path(path)
    if p.stat().st_size > MAX_PLAN_BYTES:
        raise ValueError("Preregistration exceeds size limit")
    try:
        plan = json.loads(p.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as e:
        raise ValueError("Invalid UTF-8 JSON preregistration") from e
    required = {"schema_version", "plan_id", "scope", "alignment_policy", "window_s", "limits"}
    if not isinstance(plan, dict) or set(plan) != required:
        raise ValueError("Preregistration must contain exact required fields")
    if plan["schema_version"] != "0.1.0" or plan["scope"] != "NONHUMAN_PAIRED_HEADFORM":
        raise ValueError("Unsupported plan version or scope")
    if plan["alignment_policy"] != "IDENTICAL_TIMESTAMPS_NO_POSTHOC_SHIFT":
        raise ValueError("Clock shifting/resampling cannot be optimized after observation")
    if not isinstance(plan["plan_id"], str) or not 1 <= len(plan["plan_id"]) <= 100 or any(ord(c) < 33 or ord(c) > 126 for c in plan["plan_id"]):
        raise ValueError("Invalid plan identifier")
    window = plan["window_s"]
    if not isinstance(window, list) or len(window) != 2:
        raise ValueError("Window must be a fixed [start,end] pair")
    start = _finite_number(window[0], "window start", min_value=0, max_value=60)
    end = _finite_number(window[1], "window end", min_value=0, max_value=60)
    if end <= start:
        raise ValueError("Analysis window must have positive duration")
    limits = plan["limits"]
    if not isinstance(limits, dict) or set(limits) != set(COMPONENTS):
        raise ValueError("Each component must have preregistered limits")
    for name, thresholds in limits.items():
        if not isinstance(thresholds, dict) or set(thresholds) != {"max_peak_increase_pct", "max_rms_increase_pct"}:
            raise ValueError(f"Incomplete limits for {name}")
        for label, value in thresholds.items():
            _finite_number(value, f"{name}.{label}", min_value=-100, max_value=1000)
    return plan


def _manifest(path):
    p = Path(path)
    if p.stat().st_size > MAX_PLAN_BYTES:
        raise ValueError("Manifest too large")
    return _metadata(json.loads(p.read_text(encoding="utf-8")))


def _trace_metrics(times, values):
    peak = max(values)
    index = values.index(peak)
    duration = times[-1] - times[0]
    squared_integral = sum((values[i]**2 + values[i+1]**2) * (times[i+1]-times[i])/2 for i in range(len(times)-1))
    rms = math.sqrt(squared_integral / duration)
    impulse = sum((values[i] + values[i+1]) * (times[i+1]-times[i])/2 for i in range(len(times)-1))
    return {"peak": peak, "peak_time_s": times[index], "rms": rms,
            "trapezoid_integral": impulse, "window_duration_s": duration}


def _shape_metrics(reference, candidate):
    rms = math.sqrt(sum(x*x for x in reference) / len(reference))
    rmse = math.sqrt(sum((x-y)**2 for x,y in zip(reference,candidate)) / len(reference))
    a = sum(reference)/len(reference)
    b = sum(candidate)/len(candidate)
    covariance = sum((x-a)*(y-b) for x,y in zip(reference,candidate))
    vx = sum((x-a)**2 for x in reference)
    vy = sum((x-b)**2 for x in candidate)
    return {"normalized_rmse_to_reference_rms": rmse/rms if rms > 0 else None,
            "pearson_correlation": covariance/math.sqrt(vx*vy) if vx > 0 and vy > 0 else None}


def evaluate_pair(plan_path, reference, candidate):
    """Return aggregate metrics and hashes only. File triples are profile/manifest/csv."""
    plan = read_plan(plan_path)
    info0, info1 = validate_intake(*reference), validate_intake(*candidate)
    for info in (info0,info1):
        if not info["quality_structural_pass"]:
            raise ValueError("Missing sample or sensor saturation blocks waveform analysis")
        if info["source_origin"] == "NONHUMAN_INSTRUMENTED_HEADFORM" and info["intake_status"] != "REVIEW_REQUIRED":
            raise ValueError("Unreviewed real-data rights prevent paired waveform analysis")
    if info0["source_origin"] != info1["source_origin"]:
        raise ValueError("Cannot mix synthetic and nonhuman measured acquisitions")
    m0, m1 = _manifest(reference[1]), _manifest(candidate[1])
    p0, p1 = _read_profile(reference[0]), _read_profile(candidate[0])
    if (m0["condition"], m1["condition"]) != ("reference", "candidate"):
        raise ValueError("Required designated reference/candidate pairing")
    for field in ("origin", "impact_location", "rig_id", "coordinate_frame", "test_protocol", "units"):
        if m0[field] != m1[field]:
            raise ValueError(f"Pair metadata mismatch: {field}")
    for field in ("filter_reference", "gravity_reference", "clock_reference", "frame_reference"):
        if p0["acquisition"][field] != p1["acquisition"][field]:
            raise ValueError(f"Pair acquisition mismatch: {field}")
    if abs(p0["acquisition"]["impact_speed_m_s"]-p1["acquisition"]["impact_speed_m_s"]) > .05:
        raise ValueError("Impact speeds differ by more than 0.05 m/s")
    if p0["acquisition"]["replicate_id"] == p1["acquisition"]["replicate_id"]:
        raise ValueError("Same replicate cannot be compared to itself")
    if info0["bundle_sha256"] == info1["bundle_sha256"]:
        raise ValueError("Both arms cannot reference the same file")
    times, ref_values, cand_values = [], {k:[] for k in COMPONENTS}, {k:[] for k in COMPONENTS}
    seen = 0
    lower, upper = plan["window_s"]
    from itertools import zip_longest
    for a, b in zip_longest(_iter_samples(reference[2]), _iter_samples(candidate[2])):
        if a is None or b is None:
            raise ValueError("Unequal trace length")
        seen += 1
        if abs(a[0]-b[0]) > 1e-9:
            raise ValueError("Clock mismatch; no posthoc alignment or resampling")
        if lower <= a[0] <= upper:
            times.append(a[0])
            for key, (i,j,_) in COMPONENTS.items():
                ref_values[key].append(_norm3(a[i:j]))
                cand_values[key].append(_norm3(b[i:j]))
    if seen != info0["trace_count"] or seen != info1["trace_count"]:
        raise ValueError("Trace count mismatch")
    if len(times) < 3 or times[0] > lower + 1.1/p0["acquisition"]["sampling_hz"] or times[-1] < upper - 1.1/p0["acquisition"]["sampling_hz"]:
        raise ValueError("Preregistered window not fully covered with three or more samples")
    intervals = [t2-t1 for t1,t2 in zip(times,times[1:])]
    expected_interval = 1.0 / p0["acquisition"]["sampling_hz"]
    if any(abs(dt / expected_interval - 1) > .05 for dt in intervals):
        raise ValueError("Waveform clock jitter exceeds five percent; resampling requires separate protocol")
    alerts = []
    component_results = {}
    for key, (_, _, uncertainty_key) in COMPONENTS.items():
        x, y = ref_values[key], cand_values[key]
        reference_metrics, candidate_metrics = _trace_metrics(times,x), _trace_metrics(times,y)
        if reference_metrics["peak"] <= 0 or reference_metrics["rms"] <= 0:
            raise ValueError("Zero reference response prevents percentage comparison")
        changes = {metric:100*(candidate_metrics[metric]/reference_metrics[metric]-1) for metric in ("peak","rms")}
        u0 = math.sqrt(3)*p0["uncertainty"][uncertainty_key]
        u1 = math.sqrt(3)*p1["uncertainty"][uncertainty_key]
        intervals = {"reference":[max(0,reference_metrics["peak"]-u0),reference_metrics["peak"]+u0],
                     "candidate":[max(0,candidate_metrics["peak"]-u1),candidate_metrics["peak"]+u1]}
        direction = ("candidate_lower" if intervals["candidate"][1]<intervals["reference"][0] else
                     "candidate_higher" if intervals["candidate"][0]>intervals["reference"][1] else "uncertainty_overlap")
        for field, threshold_key in (("peak","max_peak_increase_pct"),("rms","max_rms_increase_pct")):
            if changes[field] > plan["limits"][key][threshold_key]:
                alerts.append(f"{key}:{field.upper()}_INCREASE_EXCEEDS_SCREEN")
        component_results[key] = {"reference":reference_metrics,"candidate":candidate_metrics,
                                  "changes_percent":changes,"shape_comparison":_shape_metrics(x,y),
                                  "declared_component_uncertainty_peak_intervals":intervals,
                                  "peak_interval_relation":direction}
    demo = info0["source_origin"] == "SYNTHETIC_HEADFORM_FIXTURE"
    blockers = ["S0_UNVALIDATED_MODEL", "NO_CLINICAL_OR_PROTECTIVE_PERFORMANCE_INFERENCE", "INDEPENDENT_CALIBRATION_AND_LAB_REVIEW_REQUIRED"]
    if demo: blockers.append("SYNTHETIC_ONLY")
    return {"schema_version":"0.1.0", "scientific_evidence_level":"S0",
            "status":"SYNTHETIC_SCREEN_ONLY" if demo else "EXPLORATORY_NONHUMAN_LAB_SCREEN_ONLY",
            "screen":"ALERTS_OBSERVED" if alerts else "NO_PREREGISTERED_ALERTS_OBSERVED",
            "alerts": sorted(alerts), "sample_count":len(times),
            "plan_sha256":canonical_hash(plan),"reference_sha256":info0["reference_identity_sha256"],
            "candidate_sha256":info1["reference_identity_sha256"],"metrics":component_results,
            "blockers":blockers,
            "interpretation":"Descriptive paired nonhuman headform traces only; screens are not helmet acceptance, model calibration, or concussion prevention evidence."}


def model_vs_measurement_gate(model_metadata: dict, measurement_summary: dict) -> dict:
    """Explicitly block unqualified numerical-to-real-data comparisons."""
    if not isinstance(model_metadata,dict) or not isinstance(measurement_summary,dict):
        raise ValueError("Expected model and measurement metadata objects")
    reasons = ["ONE_AXIS_MODEL_LACKS_VERIFIED_3D_TO_1D_FRAME_MAPPING",
               "MISSING_INDEPENDENT_CALIBRATION_AND_VALIDATION_PROTOCOL",
               "NO_FIXED_HOLDOUT_DATASET_OR_ACCEPTANCE_THRESHOLDS"]
    if measurement_summary.get("source_origin") != "NONHUMAN_INSTRUMENTED_HEADFORM":
        reasons.append("REAL_HEADFORM_DATA_UNAVAILABLE")
    return {"scientific_evidence_level":"S0", "status":"BLOCKED",
            "reasons":reasons, "model_identity_sha256":canonical_hash(model_metadata),
            "measurement_identity_sha256":canonical_hash(measurement_summary),
            "note":"No direct comparison permitted without preregistered coordinate transformation, calibrated physical data, and lab review."}
