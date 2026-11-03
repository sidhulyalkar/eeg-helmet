"""S0-only independent-unit and confounding preflight for nonhuman impact studies.

No measurements, effect estimates, p-values, physical calibration, external file
reads, authorization or clinical/protective-performance inference.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path

SCHEMA = "neuroshield.study-design/0.1"
MAX_BYTES = 131_072
MAX_BLOCKS = 96
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{2,79}\Z")
HEX = re.compile(r"[0-9a-f]{64}\Z")
ARM = {"reference", "candidate"}
OUTCOMES = {
    "head_peak_linear_acceleration_m_s2",
    "head_peak_angular_acceleration_rad_s2",
    "head_peak_angular_velocity_rad_s",
    "upper_neck_peak_force_n",
    "upper_neck_peak_moment_n_m",
}
PLAN_KEYS = {"schema_version", "study_id", "question", "origin", "analysis_unit",
             "preregistration_digest_sha256", "preregistration_status",
             "assignment_policy", "primary_outcome", "secondary_outcomes",
             "max_speed_deviation_m_s", "blocks"}
BLOCK_KEYS = {"block_id", "stratum_id", "rig_id", "headform_id", "test_day_id",
              "impact_location", "impact_angle_deg", "temperature_c", "target_speed_m_s", "trials"}
TRIAL_KEYS = {"trial_id", "arm", "order", "measured_speed_m_s", "helmet_unit_id",
              "acquisition_id", "raw_sha256"}
ORIGINS = {"SYNTHETIC_HEADFORM_FIXTURE", "NONHUMAN_INSTRUMENTED_HEADFORM"}


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key in study plan")
        result[key] = value
    return result


def _finite(value, label, lo, hi):
    if type(value) not in (int, float) or not math.isfinite(value) or not lo <= value <= hi:
        raise ValueError(f"{label} must be finite and within [{lo}, {hi}]")
    return float(value)


def _token(value, label):
    if not isinstance(value, str) or TOKEN.fullmatch(value) is None:
        raise ValueError(f"Invalid {label}: use only nonidentifying opaque tokens")
    return value


def _exact(value, keys, name):
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{name} must have exactly the declared fields")
    return value


def read_study(path: str | Path) -> dict:
    path = Path(path)
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= MAX_BYTES:
        raise ValueError("Missing, symlinked or oversized study plan")
    try:
        obj = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_pairs,
                         parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Non-finite JSON")))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Study plan must be valid UTF-8 JSON") from exc
    return validate_study(obj)


def validate_study(obj: dict) -> dict:
    _exact(obj, PLAN_KEYS, "study plan")
    if obj["schema_version"] != SCHEMA or obj["origin"] not in ORIGINS:
        raise ValueError("Only explicit nonhuman or synthetic study plans are supported")
    _token(obj["study_id"], "study ID")
    if not isinstance(obj["question"], str) or not 40 <= len(obj["question"]) <= 500 or "\n" in obj["question"]:
        raise ValueError("Require a falsifiable research question")
    if obj["analysis_unit"] != "matched_impact_block":
        raise ValueError("The analysis unit must be the matched impact block, not individual time samples")
    if not isinstance(obj["preregistration_digest_sha256"], str) or not HEX.fullmatch(obj["preregistration_digest_sha256"]):
        raise ValueError("Require a pinned independent plan digest")
    if obj["preregistration_status"] != "AUTHOR_DECLARED_TIMESTAMP_UNVERIFIED":
        raise ValueError("No independent preregistration timing or authorization established")
    if obj["assignment_policy"] not in {"counterbalanced_declared", "fixed_order_declared"}:
        raise ValueError("Study assignment must be explicitly declared")
    if obj["primary_outcome"] not in OUTCOMES:
        raise ValueError("Primary outcome must be an allowlisted physical metric")
    secondary = obj["secondary_outcomes"]
    if (not isinstance(secondary, list) or not secondary or len(secondary) > 4
        or any(not isinstance(x, str) for x in secondary)
        or len(set(secondary)) != len(secondary) or obj["primary_outcome"] in secondary
        or any(x not in OUTCOMES for x in secondary)):
        raise ValueError("Secondary physical outcomes must be distinct and allowlisted")
    tol = _finite(obj["max_speed_deviation_m_s"], "speed tolerance", 0, 0.5)
    blocks = obj["blocks"]
    if not isinstance(blocks, list) or not 2 <= len(blocks) <= MAX_BLOCKS:
        raise ValueError("Study requires 2..96 matched blocks")
    ids = {"block": set(), "trial": set(), "acquisition": set(), "raw": set()}
    grouped = defaultdict(list)
    for b in blocks:
        _exact(b, BLOCK_KEYS, "matched block")
        for key in ("block_id", "stratum_id", "rig_id", "headform_id", "test_day_id", "impact_location"):
            _token(b[key], key)
        if b["block_id"] in ids["block"]:
            raise ValueError("Duplicate block ID")
        ids["block"].add(b["block_id"])
        _finite(b["impact_angle_deg"], "impact angle", -180, 180)
        _finite(b["temperature_c"], "test temperature", -40, 100)
        _finite(b["target_speed_m_s"], "target speed", .01, 100)
        trials = b["trials"]
        if not isinstance(trials, list) or len(trials) != 2 or any(not isinstance(v, dict) for v in trials):
            raise ValueError("Every block must contain exactly two trial objects")
        if any(type(v.get("arm")) is not str for v in trials) or {v["arm"] for v in trials} != ARM:
            raise ValueError("Each block needs exactly one reference and one candidate trial")
        if any(type(v.get("order")) is not int for v in trials) or {v["order"] for v in trials} != {1, 2}:
            raise ValueError("Each block needs distinct order 1 and 2")
        for trial in trials:
            _exact(trial, TRIAL_KEYS, "impact trial")
            for key in ("trial_id", "helmet_unit_id", "acquisition_id"):
                _token(trial[key], key)
            raw_hash = trial["raw_sha256"]
            if not isinstance(raw_hash, str) or not HEX.fullmatch(raw_hash):
                raise ValueError("Every trial requires a raw acquisition SHA-256 identity")
            measured = _finite(trial["measured_speed_m_s"], "impact speed", .01, 100)
            if abs(measured - b["target_speed_m_s"]) > tol + 1e-10:
                raise ValueError("Impact speed exceeded prespecified tolerance")
            for name, value in (("trial", trial["trial_id"]),
                                ("acquisition", trial["acquisition_id"]), ("raw", raw_hash)):
                if value in ids[name]:
                    raise ValueError(f"Repeated {name} identity across impacts")
                ids[name].add(value)
        if abs(trials[0]["measured_speed_m_s"] - trials[1]["measured_speed_m_s"]) > tol + 1e-10:
            raise ValueError("Matched impact speeds differ beyond tolerance")
        grouped[b["stratum_id"]].append(b)
    for _, group in grouped.items():
        first = group[0]
        for b in group[1:]:
            if (b["impact_location"] != first["impact_location"]
                or abs(b["impact_angle_deg"] - first["impact_angle_deg"]) > 1e-8
                or abs(b["target_speed_m_s"] - first["target_speed_m_s"]) > 1e-8
                or abs(b["temperature_c"] - first["temperature_c"]) > 2):
                raise ValueError("Incompatible apparatus/impact conditions pooled within stratum")
    return obj


def evaluate_design(obj: dict) -> dict:
    """Diagnostics on *declared metadata* only. No measurements or p-values."""
    obj = validate_study(obj)
    grouped = defaultdict(list)
    for b in obj["blocks"]:
        grouped[b["stratum_id"]].append(b)
    result = []
    all_warnings = set()
    for stratum, group in sorted(grouped.items()):
        orders = [next(t["arm"] for t in b["trials"] if t["order"] == 1) for b in group]
        days = {b["test_day_id"] for b in group}
        headforms = {b["headform_id"] for b in group}
        rigs = {b["rig_id"] for b in group}
        helmets = {arm: [t["helmet_unit_id"] for b in group for t in b["trials"] if t["arm"] == arm]
                   for arm in sorted(ARM)}
        warnings = []
        if len(group) < 3:
            warnings.append("FEWER_THAN_THREE_MATCHED_BLOCKS")
        if len(set(orders)) < 2:
            warnings.append("ARM_ORDER_CONFOUNDED")
        if obj["assignment_policy"] == "fixed_order_declared":
            warnings.append("NO_RANDOMIZATION_CLAIM_SUPPORTED")
        if len(days) == 1:
            warnings.append("SINGLE_DAY_CLUSTER")
        if len(headforms) == 1:
            warnings.append("SINGLE_HEADFORM_CLUSTER")
        if len(rigs) == 1:
            warnings.append("SINGLE_RIG_GENERALIZATION_LIMIT")
        if any(len(set(ids)) < len(ids) for ids in helmets.values()):
            warnings.append("HELMET_UNITS_REUSED_CLUSTERED_RESPONSES")
        warnings.append("CARRYOVER_AND_WEAR_UNVERIFIED")
        all_warnings.update(warnings)
        result.append({"stratum_id": stratum, "matched_block_count": len(group),
                       "impact_trials_count": 2 * len(group),
                       "first_arm_counts": {arm: orders.count(arm) for arm in sorted(ARM)},
                       "test_day_cluster_count": len(days), "headform_cluster_count": len(headforms),
                       "rig_cluster_count": len(rigs),
                       "distinct_helmet_units_per_arm": {arm: len(set(ids)) for arm, ids in helmets.items()},
                       "warnings": sorted(warnings), "independent_samples_inferred": False,
                       "significance_test_performed": False})
    encoded = json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return {"schema_version": SCHEMA, "status": "DESCRIPTIVE_DESIGN_REVIEW_REQUIRED",
            "scientific_evidence_level": "S0",
            "origin_declaration": obj["origin"], "source_identity_verified": False,
            "preregistration_timing_verified": False, "random_assignment_verified": False,
            "independent_physical_validation": False, "data_import_authorized": False,
            "analysis_unit": "matched_impact_block",
            "primary_outcome": obj["primary_outcome"], "secondary_outcomes": obj["secondary_outcomes"],
            "study_plan_sha256": hashlib.sha256(encoded).hexdigest(),
            "block_count": len(obj["blocks"]), "strata_count": len(result),
            "strata": result, "warnings": sorted(all_warnings),
            "blockers": ["UNVERIFIED_SOURCE_AND_CALIBRATION", "NO_AUTHENTICATED_PREREGISTRATION",
                         "ASSIGNMENT_AND_TEST_ORDER_NOT_INDEPENDENTLY_VERIFIED",
                         "NO_EMPIRICAL_MODEL_OR_PROTECTIVE_SAFETY_VALIDATION"],
            "interpretation": "Design metadata and clustering only. No measured effects, independent trial inference, confidence intervals, significance test, human recordings or protection claims. Impacts sharing rigs, headforms and helmets may have correlated outcomes."}


def main(argv=None):
    p = argparse.ArgumentParser(description="Offline matched-nonhuman impact study design review; evidence S0")
    p.add_argument("study_plan", type=Path)
    p.add_argument("--out", type=Path)
    args = p.parse_args(argv)
    try:
        report = evaluate_design(read_study(args.study_plan))
        serialized = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
        if args.out is None:
            print(serialized, end="")
        else:
            if args.out.exists() or args.out.is_symlink() or args.out.resolve() == args.study_plan.resolve():
                raise ValueError("Output must be a new file distinct from input")
            with args.out.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(serialized)
    except (ValueError, OSError, TypeError, KeyError) as exc:
        p.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
