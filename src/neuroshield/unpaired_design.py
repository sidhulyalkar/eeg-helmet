"""S0-only review of UNPAIRED nonhuman impact experiment design metadata.

Counts are not evidence for causal effects. This tool reads no samples, performs
no statistical inference, and cannot authenticate source, calibration or rights.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

SCHEMA = "neuroshield.unpaired-design/0.1"
MAX_BYTES = 131_072
MAX_TRIALS = 120
MAX_STRATA = 16
TOKEN = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9._-]{2,79}\Z")
HEX = re.compile(r"[0-9a-f]{64}\Z")
FIELDS = {"schema_version", "study_id", "question", "origin", "analysis_unit",
          "comparison_factor", "comparison_levels", "stratification_factor",
          "strata", "planned_trial_count", "preregistration_digest_sha256",
          "preregistration_status", "assignment_status", "nominal_speed_m_s",
          "speed_tolerance_m_s", "angle_tolerance_deg", "primary_outcome",
          "secondary_outcomes", "trials"}
TRIAL_FIELDS = {"trial_id", "acquisition_id", "raw_sha256", "run_order",
                "record_status", "record_reason", "factor_level", "stratum_id",
                "impact_angle_deg", "impact_speed_m_s", "rig_id", "headform_id",
                "helmet_unit_id", "test_day_id"}
STATUSES = {"RECORDED", "FAILED", "EXCLUDED", "METADATA_ONLY"}
REASONS = {
    "RECORDED": {"NONE"},
    "FAILED": {"SENSOR_FAILURE", "APPARATUS_FAILURE", "PROTOCOL_DEVIATION",
               "UNKNOWN_FAILURE"},
    "EXCLUDED": {"PREREGISTERED_EXCLUSION", "POSTHOC_EXCLUSION",
                 "UNKNOWN_EXCLUSION"},
    "METADATA_ONLY": {"SOURCE_NOT_ACQUIRED"},
}
METRICS = {
    "head_peak_linear_acceleration_m_s2",
    "head_peak_angular_acceleration_rad_s2",
    "head_peak_angular_velocity_rad_s",
    "upper_neck_peak_force_n",
    "upper_neck_peak_moment_n_m",
}


def _unique(pairs):
    obj = {}
    for k, v in pairs:
        if k in obj:
            raise ValueError("Duplicate JSON key in study design")
        obj[k] = v
    return obj


def _token(s, label):
    if not isinstance(s, str) or TOKEN.fullmatch(s) is None:
        raise ValueError(f"{label} must be an opaque, safe nonidentifying identifier")
    return s


def _number(value, label, lo, hi, *, missing=False):
    if value is None and missing:
        return None
    if type(value) not in (float, int) or not math.isfinite(value) or not lo <= value <= hi:
        raise ValueError(f"{label} must be finite within [{lo}, {hi}]")
    return float(value)


def _exact(value, fields, label):
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{label} must contain exactly the allowed fields")
    return value


def read_plan(path: str | Path) -> dict:
    path = Path(path)
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= MAX_BYTES:
        raise ValueError("Study design file missing, symlinked or oversized")
    try:
        record = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique,
                            parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))
    except (UnicodeError, OSError, json.JSONDecodeError) as exc:
        raise ValueError("Study design must be valid UTF-8 JSON") from exc
    return validate_plan(record)


def validate_plan(plan: dict) -> dict:
    _exact(plan, FIELDS, "study design")
    if (plan["schema_version"] != SCHEMA or plan["origin"] not in
            {"NONHUMAN_INSTRUMENTED_HEADFORM", "SYNTHETIC_HEADFORM_FIXTURE"}):
        raise ValueError("Only explicit synthetic/nonhuman unpaired designs are supported")
    _token(plan["study_id"], "study ID")
    if not isinstance(plan["question"], str) or not 40 <= len(plan["question"]) <= 500 or "\n" in plan["question"]:
        raise ValueError("Require a substantive, falsifiable scientific question")
    if plan["analysis_unit"] != "physical_impact_trial":
        raise ValueError("Physical impact trials, never signal samples, are the study units")
    for label in ("comparison_factor", "stratification_factor"):
        _token(plan[label], label)
    if plan["comparison_factor"] == plan["stratification_factor"]:
        raise ValueError("Comparison and stratification factors must differ")
    levels = plan["comparison_levels"]
    if (not isinstance(levels, list) or len(levels) != 2
            or any(not isinstance(x, str) for x in levels)
            or any(TOKEN.fullmatch(x) is None for x in levels)
            or levels[0] == levels[1]):
        raise ValueError("Exactly two distinct declared comparison levels required")
    strata = plan["strata"]
    if (not isinstance(strata, list) or not 1 <= len(strata) <= MAX_STRATA
            or any(not isinstance(s, str) for s in strata)
            or any(TOKEN.fullmatch(s) is None for s in strata)
            or len(strata) != len(set(strata))):
        raise ValueError("Unique known experimental strata required")
    if type(plan["planned_trial_count"]) is not int or not 2 <= plan["planned_trial_count"] <= MAX_TRIALS:
        raise ValueError("Require a bounded, prespecified trial count")
    digest = plan["preregistration_digest_sha256"]
    if not isinstance(digest, str) or HEX.fullmatch(digest) is None:
        raise ValueError("Require a format-valid declared protocol digest")
    if plan["preregistration_status"] != "AUTHOR_DECLARED_TIMESTAMP_UNVERIFIED":
        raise ValueError("Cannot assert authenticated preregistration chronology")
    if plan["assignment_status"] not in {"NOT_RECORDED", "AUTHOR_DECLARED_UNVERIFIED"}:
        raise ValueError("Assignment must remain explicitly unverified")
    nominal = _number(plan["nominal_speed_m_s"], "nominal speed", .01, 100)
    speed_tolerance = _number(plan["speed_tolerance_m_s"], "speed tolerance", 0, 2)
    angle_tolerance = _number(plan["angle_tolerance_deg"], "angle tolerance", 0, 10)
    if plan["primary_outcome"] not in METRICS:
        raise ValueError("Primary outcome must be a named measured physical quantity")
    secondary = plan["secondary_outcomes"]
    if (not isinstance(secondary, list) or not 1 <= len(secondary) <= 4
            or any(not isinstance(s, str) for s in secondary)
            or len(secondary) != len(set(secondary))
            or any(s not in METRICS for s in secondary)
            or plan["primary_outcome"] in secondary):
        raise ValueError("Secondary outcomes must be distinct, physically defined quantities")
    trials = plan["trials"]
    if not isinstance(trials, list) or len(trials) != plan["planned_trial_count"]:
        raise ValueError("Every planned trial, including failures/exclusions, must be represented")
    seen = {"trial_id": set(), "acquisition_id": set(), "raw_sha256": set(), "run_order": set()}
    grouped = defaultdict(list)
    for trial in trials:
        _exact(trial, TRIAL_FIELDS, "trial metadata")
        for field in ("trial_id", "acquisition_id", "rig_id", "headform_id", "test_day_id"):
            _token(trial[field], field)
        if trial["helmet_unit_id"] is not None:
            _token(trial["helmet_unit_id"], "helmet unit")
        for field in ("trial_id", "acquisition_id"):
            if trial[field] in seen[field]:
                raise ValueError("Repeated trial or acquisition identity")
            seen[field].add(trial[field])
        if trial["factor_level"] not in levels or trial["stratum_id"] not in strata:
            raise ValueError("Undeclared factor level or experimental stratum")
        status = trial["record_status"]
        if not isinstance(status, str) or status not in STATUSES:
            raise ValueError("Invalid trial disposition")
        if trial["record_reason"] not in REASONS[status]:
            raise ValueError("Incompatible trial status and disposition reason")
        raw = trial["raw_sha256"]
        if raw is not None:
            if not isinstance(raw, str) or HEX.fullmatch(raw) is None:
                raise ValueError("Raw acquisition identity must be SHA-256 or null")
            if raw in seen["raw_sha256"]:
                raise ValueError("Repeated raw acquisition digest")
            seen["raw_sha256"].add(raw)
        if status == "RECORDED" and raw is None:
            raise ValueError("Recorded trials must declare exact data identity")
        if status == "METADATA_ONLY" and raw is not None:
            raise ValueError("Metadata-only trials may not pretend to hold raw files")
        order = trial["run_order"]
        if order is not None:
            if type(order) is not int or not 1 <= order <= len(trials) or order in seen["run_order"]:
                raise ValueError("Run order must be unique, positive, within planned count")
            seen["run_order"].add(order)
        angle = _number(trial["impact_angle_deg"], "impact angle", -180, 180, missing=True)
        speed = _number(trial["impact_speed_m_s"], "impact speed", 0, 100, missing=True)
        if speed is not None and abs(speed - nominal) > speed_tolerance + 1e-9:
            raise ValueError("Declared impact speed outside prespecified deviation")
        grouped[trial["stratum_id"]].append(angle)
    for key, observed in grouped.items():
        known = [x for x in observed if x is not None]
        if known and max(known) - min(known) > angle_tolerance + 1e-9:
            raise ValueError(f"Incompatible impact angles pooled in stratum {key}")
    return plan


def evaluate_design(plan: dict) -> dict:
    plan = validate_plan(plan)
    levels = plan["comparison_levels"]
    strata = []
    study_warnings = set()
    recorded_count = 0
    for name in plan["strata"]:
        subset = [t for t in plan["trials"] if t["stratum_id"] == name]
        cells = []
        count = {}
        for level in levels:
            trials = [t for t in subset if t["factor_level"] == level]
            n = Counter(x["record_status"] for x in trials)
            recorded_count += n["RECORDED"]
            count[level] = len(trials)
            headforms = {x["headform_id"] for x in trials}
            rigs = {x["rig_id"] for x in trials}
            days = {x["test_day_id"] for x in trials}
            helmets = [x["helmet_unit_id"] for x in trials if x["helmet_unit_id"] is not None]
            warnings = []
            if len(trials) == 0:
                warnings.append("EMPTY_FACTOR_CELL")
            if n["RECORDED"] < 2:
                warnings.append("FEWER_THAN_TWO_RECORDED_IMPACTS")
            if n["FAILED"] or n["EXCLUDED"]:
                warnings.append("FAILURES_OR_EXCLUSIONS_PRESERVED")
            if n["EXCLUDED"]:
                warnings.append("EXCLUSION_MAY_BIAS_ANALYSIS")
            if len(helmets) > len(set(helmets)):
                warnings.append("REPEATED_HELMET_UNIT_WITHIN_CELL")
            if trials and (len(headforms) == 1 or len(days) == 1 or len(rigs) == 1):
                warnings.append("LIMITED_LAB_CLUSTER_DIVERSITY")
            if any(x["run_order"] is None for x in trials):
                warnings.append("UNKNOWN_OR_PARTIAL_RUN_ORDER")
            if any(x["impact_angle_deg"] is None or x["impact_speed_m_s"] is None for x in trials):
                warnings.append("INCOMPLETE_IMPACT_METADATA")
            study_warnings.update(warnings)
            cells.append({"factor_level": level, "planned_trial_count": len(trials),
                          "record_status_counts": {s: n[s] for s in sorted(STATUSES)},
                          "headform_cluster_count": len(headforms),
                          "rig_cluster_count": len(rigs), "testing_day_cluster_count": len(days),
                          "distinct_declared_helmet_units": len(set(helmets)),
                          "warnings": sorted(warnings)})
        if count[levels[0]] == 0 or count[levels[1]] == 0:
            study_warnings.add("NO_WITHIN_STRATUM_TWO_LEVEL_COMPARISON")
        if subset and all(t["run_order"] is not None for t in subset) and all(count.values()):
            seq = {level: [t["run_order"] for t in subset if t["factor_level"] == level] for level in levels}
            if max(seq[levels[0]]) < min(seq[levels[1]]) or max(seq[levels[1]]) < min(seq[levels[0]]):
                study_warnings.add("FACTOR_CONFOUNDED_WITH_SEQUENTIAL_TEST_ORDER")
        elif subset:
            study_warnings.add("RUN_ORDER_NOT_FULLY_DECLARED")
        strata.append({"stratum_id": name, "total_declared_trials": len(subset), "cells": cells,
                       "descriptive_two_level_coverage_only": all(count.values()),
                       "effect_estimation_authorized": False})
    if len(plan["strata"]) > 1:
        study_warnings.add("NO_CROSS_STRATUM_POOLING_WITHOUT_NEW_PROTOCOL")
    if any(t["record_status"] == "METADATA_ONLY" for t in plan["trials"]):
        study_warnings.add("UNACQUIRED_RAW_MEASUREMENTS")
    if len({t["headform_id"] for t in plan["trials"]}) == 1:
        study_warnings.add("SINGLE_HEADFORM_GENERALIZABILITY_LIMIT")
    if len({t["rig_id"] for t in plan["trials"]}) == 1:
        study_warnings.add("SINGLE_RIG_GENERALIZABILITY_LIMIT")
    scientific = json.dumps(plan, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return {
        "schema_version": SCHEMA, "status": "FACTORIAL_DESIGN_REVIEW_ONLY",
        "scientific_evidence_level": "S0", "input_origin_declared": plan["origin"],
        "study_plan_sha256": hashlib.sha256(scientific).hexdigest(),
        "analysis_unit": "physical_impact_trial",
        "preregistration_timing_verified": False, "randomization_verified": False,
        "source_identity_verified": False, "calibration_verified": False,
        "data_import_authorized": False, "causal_effect_authorized": False,
        "independent_samples_inferred": False, "statistical_tests_performed": False,
        "factor": plan["comparison_factor"], "levels": levels,
        "stratification_factor": plan["stratification_factor"],
        "planned_trial_count": len(plan["trials"]), "recorded_trial_count": recorded_count,
        "strata": strata, "warnings": sorted(study_warnings),
        "blockers": ["NO_AUTHENTICATED_PREREGISTRATION_OR_ASSIGNMENT",
                     "INDEPENDENT_SOURCE_AND_CALIBRATION_REVIEW_MISSING",
                     "NO_PHYSICAL_MODEL_FIT_OR_PROTECTIVE_SAFETY_CLAIMS"],
        "interpretation": "Unpaired observational or factorial metadata screen only. Empty cells, repeated equipment and missing trials must not be hidden. No estimate of helmet protection, sample-level pseudoreplication, p-value, uncertainty interval, causal attribution or medical decision."}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Offline S0 review for unpaired nonhuman factorial study designs")
    p.add_argument("plan", type=Path)
    p.add_argument("--out", type=Path)
    args = p.parse_args(argv)
    try:
        report = evaluate_design(read_plan(args.plan))
        encoded = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
        if args.out is None:
            print(encoded, end="")
        else:
            if args.out.exists() or args.out.is_symlink() or args.out.resolve() == args.plan.resolve():
                raise ValueError("Cannot overwrite existing output or input")
            with args.out.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(encoded)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        p.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
