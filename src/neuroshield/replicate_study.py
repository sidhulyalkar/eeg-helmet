"""Local-only replicate-level screening of independent NONHUMAN headform trials.

A descriptive synthetic/laboratory research workflow, never a helmet safety rating.
The independent observation is the impact TRIAL, not individual sampled timepoints.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path

from .bench_intake import _read_profile, compare_paired_trials
from .headform import _metadata
from .provenance import canonical_hash

SCHEMA = "neuroshield.replicate-study/0.1"
CHANNELS = (
    "resultant_linear_acceleration_m_s2",
    "resultant_angular_acceleration_rad_s2",
    "resultant_angular_velocity_rad_s",
)
MAX_PLAN_BYTES = 131_072
MAX_PAIRS = 50
KEYS = {"schema_version", "plan_id", "scope", "expected_origin", "protocol", "impact_location", "rig_id", "target_speed_m_s", "speed_tolerance_m_s", "max_peak_regression_percent", "pairs"}
TRIPLE = {"profile", "manifest", "csv"}


def _finite(value: object, label: str, lo: float, hi: float) -> float:
    if type(value) not in (int, float) or not math.isfinite(value) or not lo <= value <= hi:
        raise ValueError(f"{label} must be a finite number in [{lo}, {hi}]")
    return float(value)


def _label(value: object, label: str) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= 160 or not value.isascii() or any(ord(c) < 33 or ord(c) > 126 for c in value):
        raise ValueError(f"Invalid {label}")
    return value


def _safe_path(base: Path, item: object) -> Path:
    if not isinstance(item, str) or not item or len(item) > 240:
        raise ValueError("Invalid relative input path")
    relative = Path(item)
    if relative.is_absolute() or any(part in ("..", ".") for part in relative.parts) or "\\" in item or ":" in item:
        raise ValueError("Paths must be relative and cannot contain traversal components")
    if any(part.startswith(".") for part in relative.parts):
        raise ValueError("Hidden files and directories are not accepted")
    full = base / relative
    if any(node.is_symlink() for node in (full, *full.parents) if node != base.parent):
        raise ValueError("Symlinks not permitted in dataset paths")
    if not full.resolve().is_relative_to(base.resolve()):
        raise ValueError("Dataset path leaves the study directory")
    if not full.is_file():
        raise ValueError("Dataset file not found")
    return full


def _validate_plan(obj: object):
    if not isinstance(obj, dict) or set(obj) != KEYS:
        raise ValueError("Study plan requires exact fields")
    if obj["schema_version"] != SCHEMA or obj["scope"] != "NONHUMAN_PAIRED_IMPACT_TRIALS":
        raise ValueError("Unsupported study schema or scope")
    _label(obj["plan_id"], "plan identifier")
    if obj["expected_origin"] not in ("SYNTHETIC_HEADFORM_FIXTURE", "NONHUMAN_INSTRUMENTED_HEADFORM"):
        raise ValueError("Human data prohibited")
    for k in ("protocol", "impact_location", "rig_id"):
        _label(obj[k], k)
    _finite(obj["target_speed_m_s"], "target_speed_m_s", .01, 100)
    _finite(obj["speed_tolerance_m_s"], "speed_tolerance_m_s", 0, .5)
    limits = obj["max_peak_regression_percent"]
    if not isinstance(limits, dict) or set(limits) != set(CHANNELS):
        raise ValueError("Each kinematic channel requires a preregistered limit")
    for k in CHANNELS:
        _finite(limits[k], f"limit.{k}", -100, 1000)
    pairs = obj["pairs"]
    if not isinstance(pairs, list) or not 2 <= len(pairs) <= MAX_PAIRS:
        raise ValueError("At least two and at most 50 paired trials required")
    for pair in pairs:
        if not isinstance(pair, dict) or set(pair) != {"reference", "candidate"}:
            raise ValueError("Paired trial must have reference and candidate")
        for arm in pair.values():
            if not isinstance(arm, dict) or set(arm) != TRIPLE:
                raise ValueError("Each trial arm requires profile, manifest and csv")
    return obj


def read_study(path: str | Path):
    path = Path(path)
    if path.stat().st_size > MAX_PLAN_BYTES:
        raise ValueError("Study plan exceeds size limit")
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ValueError("Study plan must be valid UTF-8 JSON") from exc
    return _validate_plan(obj)


def _summary(values: list[float]) -> dict:
    return {"mean_percent": statistics.mean(values), "median_percent": statistics.median(values),
            "min_percent": min(values), "max_percent": max(values),
            "sample_sd_percent": statistics.stdev(values),
            "direction_disagrees_across_trials": any(v < 0 for v in values) and any(v > 0 for v in values)}


def evaluate_study(study_path: str | Path) -> dict:
    """Aggregate paired trials after V0.7 intake, with no sample-level pseudoreplication."""
    plan = read_study(study_path)
    base = Path(study_path).resolve().parent
    seen_data, seen_replicates, trials = set(), set(), []
    origins = set()
    acquisition_signature = None
    for pair_idx, pair in enumerate(plan["pairs"]):
        triples = {}
        for arm in ("reference", "candidate"):
            paths = {key: _safe_path(base, pair[arm][key]) for key in TRIPLE}
            p = _read_profile(paths["profile"])
            m = _metadata(json.loads(paths["manifest"].read_text(encoding="utf-8")))
            if m["test_protocol"] != plan["protocol"] or m["impact_location"] != plan["impact_location"] or m["rig_id"] != plan["rig_id"]:
                raise ValueError("Study preregistration does not match apparatus or protocol")
            if p["origin"] != plan["expected_origin"] or m["origin"] != plan["expected_origin"]:
                raise ValueError("Study origin mismatch")
            if abs(p["acquisition"]["impact_speed_m_s"] - plan["target_speed_m_s"]) > plan["speed_tolerance_m_s"] + 1e-10:
                raise ValueError("Impact speed outside preregistered tolerance")
            identity = p["source"]["raw_data_sha256"]
            if identity in seen_data:
                raise ValueError("Repeated raw acquisition used across study arms")
            seen_data.add(identity)
            rid = p["acquisition"]["replicate_id"]
            if rid in seen_replicates:
                raise ValueError("Duplicate replicate identifier")
            seen_replicates.add(rid)
            origins.add(p["origin"])
            signature = (p["acquisition"]["sampling_hz"], p["acquisition"]["filter_reference"],
                         p["acquisition"]["gravity_reference"], p["acquisition"]["clock_reference"],
                         p["acquisition"]["frame_reference"], m["coordinate_frame"],
                         json.dumps(m["units"], sort_keys=True))
            if acquisition_signature is None:
                acquisition_signature = signature
            elif signature != acquisition_signature:
                raise ValueError("Study acquisition mismatch across replicate trials")
            triples[arm] = (paths["profile"], paths["manifest"], paths["csv"])
        result = compare_paired_trials(triples["reference"], triples["candidate"])
        trials.append({"pair_number": pair_idx + 1, "reference_sha256": result["reference_sha256"],
                       "candidate_sha256": result["candidate_sha256"],
                       "peak_percent_change": {key: result["metrics"][key]["peak_percent_change"] for key in CHANNELS}})
    if len(origins) != 1:
        raise ValueError("Cannot pool synthetic and measured trials")
    metrics, alerts = {}, []
    for k in CHANNELS:
        changes = [trial["peak_percent_change"][k] for trial in trials]
        metrics[k] = _summary(changes)
        metrics[k]["preregistered_max_regression_percent"] = plan["max_peak_regression_percent"][k]
        if any(v > plan["max_peak_regression_percent"][k] for v in changes):
            alerts.append(f"{k}:ONE_OR_MORE_TRIALS_EXCEED_REGRESSION_BOUND")
    synthetic = plan["expected_origin"] == "SYNTHETIC_HEADFORM_FIXTURE"
    return {"schema_version": SCHEMA, "scientific_evidence_level": "S0", 
            "status": "SYNTHETIC_REPLICATE_DEMO" if synthetic else "EXPLORATORY_NONHUMAN_LAB_REVIEW_REQUIRED",
            "screen": "REGRESSIONS_FLAGGED" if alerts else "NO_PREDECLARED_REGRESSIONS_FLAGGED",
            "alerts": sorted(alerts), "pair_count": len(trials),
            "study_sha256": canonical_hash(plan), "metrics": metrics, "trials": trials,
            "blockers": ["INDEPENDENT_LAB_REPLICATION_AND_CALIBRATION_REVIEW_REQUIRED", "NO_INJURY_OR_SAFETY_CLAIMS", *(["SYNTHETIC_ONLY"] if synthetic else [])],
            "interpretation": "Descriptive paired-trial replication only; samples within a trial are not independent replicates. No statistical inference, protection claim, model calibration, or clinical outcome. Source declarations require independent verification."}


def main(argv=None):
    p = argparse.ArgumentParser(description="Offline multi-trial S0 nonhuman headform repeatability screen")
    p.add_argument("study", help="UTF-8 preregistration JSON plus relative local trial files")
    p.add_argument("--out", required=True, help="Write aggregate JSON, never raw traces")
    args = p.parse_args(argv)
    result = evaluate_study(args.study)
    Path(args.out).write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"{result['status']}: {result['pair_count']} pairs; screen {result['screen']}")


if __name__ == "__main__":
    main()
