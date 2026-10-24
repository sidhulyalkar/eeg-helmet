"""Local-only, nonhuman instrumented-headform intake and paired metrics.

No third-party measurement is distributed, no calibration or license is independently
verified, and no output is clinical, certification or helmet-safety evidence.
The existing v0.1 headform contract remains unchanged; this optional sidecar
adds acquisition provenance and an explicit *review* gate, never an S1 grant.
"""
from __future__ import annotations

import csv
import json
import math
from hashlib import sha256
from pathlib import Path

from .headform import COLUMNS, validate_headform_bundle
from .provenance import canonical_hash

PROFILE_KEYS = {"schema_version", "origin", "headform_bundle_sha256", "source", "rights", "acquisition", "uncertainty"}
SOURCE_KEYS = {"source_uri", "raw_data_sha256", "protocol_reference", "laboratory_report_reference"}
RIGHTS_KEYS = {"review_status", "license_reference", "permission_evidence_reference", "redistribution_allowed"}
ACQUISITION_KEYS = {
    "trial_id", "replicate_id", "impact_speed_m_s", "sampling_hz", "filter_reference",
    "gravity_reference", "clock_reference", "frame_reference", "calibration_certificate_reference",
    "calibration_review_reference", "sensor_linear_fullscale_m_s2",
    "sensor_angular_fullscale_rad_s2", "sensor_omega_fullscale_rad_s",
}
UNCERTAINTY_KEYS = {"linear_acceleration_m_s2", "angular_acceleration_rad_s2", "angular_velocity_rad_s"}
MAX_PROFILE_SIZE = 16_384
MAX_ROWS = 300_000


def _object(value, keys, name):
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{name}: exact fields required: {sorted(keys)}")
    return value


def _identifier(value, key):
    if not isinstance(value, str) or not 1 <= len(value) <= 160 or value.strip() != value or any(ord(c) < 32 for c in value):
        raise ValueError(f"{key}: invalid identifier")
    return value


def _positive(value, key, allow_zero=False):
    if type(value) not in (int, float) or not math.isfinite(value) or (value < 0 if allow_zero else value <= 0):
        raise ValueError(f"{key}: must be finite and {'nonnegative' if allow_zero else 'positive'}")
    return float(value)


def _read_profile(path):
    path = Path(path)
    if path.stat().st_size > MAX_PROFILE_SIZE:
        raise ValueError("Profile exceeds 16 KiB")
    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid UTF-8 JSON profile") from exc
    _object(profile, PROFILE_KEYS, "profile")
    if profile["schema_version"] != "0.1.0" or profile["origin"] not in ("SYNTHETIC_HEADFORM_FIXTURE", "NONHUMAN_INSTRUMENTED_HEADFORM"):
        raise ValueError("Unsupported profile origin or schema")
    if not isinstance(profile["headform_bundle_sha256"], str) or len(profile["headform_bundle_sha256"]) != 64 or any(c not in "0123456789abcdef" for c in profile["headform_bundle_sha256"]):
        raise ValueError("Invalid bundle SHA-256")
    source = _object(profile["source"], SOURCE_KEYS, "source")
    rights = _object(profile["rights"], RIGHTS_KEYS, "rights")
    acq = _object(profile["acquisition"], ACQUISITION_KEYS, "acquisition")
    unc = _object(profile["uncertainty"], UNCERTAINTY_KEYS, "uncertainty")
    for key in SOURCE_KEYS - {"raw_data_sha256"}:
        _identifier(source[key], f"source.{key}")
    if not isinstance(source["raw_data_sha256"], str) or len(source["raw_data_sha256"]) != 64 or any(c not in "0123456789abcdef" for c in source["raw_data_sha256"]):
        raise ValueError("Invalid raw data SHA-256")
    if rights["review_status"] not in ("pending", "documented_local_analysis", "documented_redistribution"):
        raise ValueError("Unknown rights review status")
    for key in ("license_reference", "permission_evidence_reference"):
        _identifier(rights[key], f"rights.{key}")
    if type(rights["redistribution_allowed"]) is not bool:
        raise ValueError("Rights redistribution must be boolean")
    if rights["redistribution_allowed"] != (rights["review_status"] == "documented_redistribution"):
        raise ValueError("Inconsistent permission and redistribution flags")
    for key in ACQUISITION_KEYS - {"impact_speed_m_s", "sampling_hz", "sensor_linear_fullscale_m_s2", "sensor_angular_fullscale_rad_s2", "sensor_omega_fullscale_rad_s"}:
        _identifier(acq[key], f"acquisition.{key}")
    for key in ("impact_speed_m_s", "sampling_hz", "sensor_linear_fullscale_m_s2", "sensor_angular_fullscale_rad_s2", "sensor_omega_fullscale_rad_s"):
        _positive(acq[key], f"acquisition.{key}")
    if not 100 <= acq["sampling_hz"] <= 100_000:
        raise ValueError("Sampling frequency outside supported range")
    for key in UNCERTAINTY_KEYS:
        _positive(unc[key], f"uncertainty.{key}", allow_zero=False)
    if profile["origin"] == "NONHUMAN_INSTRUMENTED_HEADFORM" and not source["source_uri"].startswith("https://"):
        raise ValueError("Nonhuman external records must give an HTTPS source URI")
    return profile


def _iter_samples(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(COLUMNS):
            raise ValueError("Unexpected headform CSV columns")
        for i, row in enumerate(reader, 1):
            if i > MAX_ROWS:
                raise ValueError("Too many samples")
            yield tuple(float(row[k]) for k in COLUMNS)


def validate_intake(profile_path, manifest_path, csv_path):
    """Validate structural integrity and claimed acquisition provenance only.

    Never returns samples, original paths, filenames, subjects or instrument IDs.
    Passing is NOT calibration validation or proof of lawful reuse.
    """
    p = _read_profile(profile_path)
    bundle = validate_headform_bundle(manifest_path, csv_path)
    if p["origin"] != bundle["source_origin"]:
        raise ValueError("Headform/profile origin mismatch")
    if p["headform_bundle_sha256"] != bundle["bundle_sha256"] or p["source"]["raw_data_sha256"] != bundle["csv_sha256"]:
        raise ValueError("Headform bundle hash mismatch: file identity changed")
    hz = p["acquisition"]["sampling_hz"]
    if abs((1 / bundle["median_interval_s"]) / hz - 1) > .03:
        raise ValueError("Declared sampling frequency inconsistent with CSV clock")
    limits = [p["acquisition"][k] for k in (
        "sensor_linear_fullscale_m_s2", "sensor_angular_fullscale_rad_s2", "sensor_omega_fullscale_rad_s")]
    saturation = False
    for row in _iter_samples(csv_path):
        if any(abs(v) >= limit for v, limit in zip(row[1:4], [limits[0]] * 3)):
            saturation = True
        if any(abs(v) >= limit for v, limit in zip(row[4:7], [limits[1]] * 3)):
            saturation = True
        if any(abs(v) >= limit for v, limit in zip(row[7:10], [limits[2]] * 3)):
            saturation = True
    quality = not saturation and bundle["possible_missing_sample_gaps"] == 0
    measured = p["origin"] == "NONHUMAN_INSTRUMENTED_HEADFORM"
    has_rights = p["rights"]["review_status"] != "pending"
    blockers = []
    if not measured:
        blockers.append("SYNTHETIC_NOT_PHYSICAL_EVIDENCE")
    if not has_rights:
        blockers.append("RIGHTS_REVIEW_PENDING")
    if saturation:
        blockers.append("POSSIBLE_SENSOR_SATURATION")
    if bundle["possible_missing_sample_gaps"]:
        blockers.append("POSSIBLE_SAMPLE_GAPS")
    blockers.append("INDEPENDENT_CALIBRATION_AND_LAB_REVIEW_REQUIRED")
    return {
        "schema_version": "0.1.0", "scientific_evidence_level": "S0",
        "intake_status": "REVIEW_REQUIRED" if measured and has_rights and quality else "BLOCKED",
        "source_origin": p["origin"], "trace_count": bundle["rows"],
        "quality_structural_pass": quality, "blockers": blockers,
        "bundle_sha256": bundle["bundle_sha256"],
        "profile_sha256": canonical_hash(p),
        "reference_identity_sha256": canonical_hash({"bundle": bundle["bundle_sha256"], "profile": p}),
        "notes": "Declared provenance, licensing, and calibration references are NOT independently verified. Local nonhuman research only; no safety claims.",
    }


def _norm3(values):
    return math.sqrt(sum(x*x for x in values))


def _metric(values):
    return {"peak": max(values), "rms": math.sqrt(sum(x*x for x in values) / len(values))}


def compare_paired_trials(reference, candidate):
    """Compare local nonhuman trials on an identical acquisition clock.

    Inputs are (profile_path, headform_manifest_path, CSV_path). Report contains
    only aggregates, provenance hashes, and expressly nonclinical interpretation.
    """
    p0 = _read_profile(reference[0]); p1 = _read_profile(candidate[0])
    a = validate_intake(*reference); b = validate_intake(*candidate)
    if not a["quality_structural_pass"] or not b["quality_structural_pass"]:
        raise ValueError("Refusing paired metrics on missing samples or saturation")
    if any(x["source_origin"] == "NONHUMAN_INSTRUMENTED_HEADFORM" and x["intake_status"] != "REVIEW_REQUIRED" for x in (a,b)):
        raise ValueError("External measurement rights review pending; paired comparison blocked")
    m0 = json.loads(Path(reference[1]).read_text(encoding="utf-8"))
    m1 = json.loads(Path(candidate[1]).read_text(encoding="utf-8"))
    if m0["condition"] != "reference" or m1["condition"] != "candidate":
        raise ValueError("Must compare designated reference and candidate headforms")
    for key in ("impact_location", "rig_id", "coordinate_frame", "test_protocol", "units"):
        if m0[key] != m1[key]:
            raise ValueError(f"Paired trial mismatch: {key}")
    for key in ("filter_reference", "gravity_reference", "clock_reference", "frame_reference"):
        if p0["acquisition"][key] != p1["acquisition"][key]:
            raise ValueError(f"Acquisition mismatch: {key}")
    if p0["acquisition"]["replicate_id"] == p1["acquisition"]["replicate_id"]:
        raise ValueError("Replicate identifiers must differ")
    if abs(p0["acquisition"]["impact_speed_m_s"] - p1["acquisition"]["impact_speed_m_s"]) > .05:
        raise ValueError("Impact speeds differ by more than preregistered 0.05 m/s")
    if a["bundle_sha256"] == b["bundle_sha256"]:
        raise ValueError("Reference and candidate must be distinct data recordings")
    summaries = [[], [], []], [[], [], []]
    count = 0
    for x, y in zip(_iter_samples(reference[2]), _iter_samples(candidate[2])):
        if abs(x[0]-y[0]) > 1e-9:
            raise ValueError("Paired clock mismatch; resampling requires separately reviewed protocol")
        for dst, point in zip(summaries, (x,y)):
            for series, section in zip(dst, (point[1:4], point[4:7], point[7:10])):
                series.append(_norm3(section))
        count += 1
    if count != a["trace_count"] or count != b["trace_count"]:
        raise ValueError("Paired trial length mismatch")
    label = ("resultant_linear_acceleration_m_s2", "resultant_angular_acceleration_rad_s2", "resultant_angular_velocity_rad_s")
    uc = ("linear_acceleration_m_s2", "angular_acceleration_rad_s2", "angular_velocity_rad_s")
    metrics = {}
    for name, key, v0, v1 in zip(label, uc, *summaries):
        r, c = _metric(v0), _metric(v1)
        if r["peak"] <= 0:
            raise ValueError("Zero reference peak cannot support a relative comparison")
        u0 = math.sqrt(3) * p0["uncertainty"][key]
        u1 = math.sqrt(3) * p1["uncertainty"][key]
        metrics[name] = {"reference": r, "candidate": c,
            "peak_percent_change": 100 * (c["peak"]/r["peak"]-1),
            "conservative_peak_intervals": {
                "reference": [max(0., r["peak"] - u0), r["peak"] + u0],
                "candidate": [max(0., c["peak"] - u1), c["peak"] + u1]},
            "separation": "higher" if c["peak"] - u1 > r["peak"] + u0 else (
                "lower" if c["peak"] + u1 < r["peak"] - u0 else "overlap")}
    demo_only = any(x["source_origin"] == "SYNTHETIC_HEADFORM_FIXTURE" for x in (a,b))
    return {
        "schema_version": "0.1.0", "status": "DEMONSTRATION_ONLY" if demo_only else "EXPLORATORY_LAB_REVIEW_REQUIRED",
        "scientific_evidence_level": "S0", "samples_compared": count,
        "reference_sha256": a["reference_identity_sha256"],
        "candidate_sha256": b["reference_identity_sha256"],
        "metrics": metrics,
        "blockers": sorted(set(a["blockers"]+b["blockers"]+["REPLICATED_BLINDED_LAB_TESTS_REQUIRED", "NO_NECK_LOAD_MEASURED"])),
        "interpretation": "Descriptive headform kinematics only. No injury-risk model, certified protective effect, clinical claim, or validated calibration.",
    }
