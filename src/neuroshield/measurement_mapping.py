"""S0-only audited proposal for nonhuman head/neck measurement-column mappings.

No automatic units, sensor placement, coordinate origin shift, license decision,
real-data conversion, human recordings, or evidence-level promotion.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path

from .csv_probe import DELIMITERS, SOURCE_ID, inspect_csv, _safe_file

SCHEMA = "neuroshield.measurement-mapping/0.1"
MAX_PLAN_BYTES = 32_768
MAX_GROUPS = 5
HEX = re.compile(r"[0-9a-f]{64}\Z")
TOKEN = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9._:/#-]{2,179}\Z")
ROLE_UNITS = {
    "head_linear_acceleration": {"m/s^2": 1., "g": 9.80665},
    "head_angular_acceleration": {"rad/s^2": 1., "deg/s^2": math.pi / 180},
    "head_angular_velocity": {"rad/s": 1., "deg/s": math.pi / 180},
    "upper_neck_force": {"N": 1., "kN": 1000.},
    "upper_neck_moment": {"N*m": 1., "N*mm": .001},
}
TARGET = {
    "head_linear_acceleration": "right_handed_headform_body",
    "head_angular_acceleration": "right_handed_headform_body",
    "head_angular_velocity": "right_handed_headform_body",
    "upper_neck_force": "right_handed_upper_neck_frame",
    "upper_neck_moment": "right_handed_upper_neck_frame",
}
GROUP_KEYS = {"quantity", "indices_xyz", "header_sha256_xyz", "source_unit",
              "source_frame", "target_frame", "rotation_target_from_source",
              "measurement_point", "target_point", "calibration_reference",
              "filter_reference", "uncertainty_reference", "gravity_policy"}
PLAN_KEYS = {"schema_version", "source_id_declaration", "origin_declaration",
             "raw_file_sha256", "delimiter", "clock", "groups",
             "mapping_status", "review_reference"}
CLOCK_KEYS = {"index", "header_sha256", "unit", "time_reference"}
GRAVITY = {"not_applicable", "includes_gravity", "removed_with_documentation", "unreviewed"}


def _exact(value, keys, section):
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{section}: unexpected or missing fields")
    return value


def _positive_reference(value, label):
    if not isinstance(value, str) or not TOKEN.fullmatch(value):
        raise ValueError(f"{label}: expected opaque reference token, never a private path")
    return value


def _hash(value, label):
    if not isinstance(value, str) or not HEX.fullmatch(value):
        raise ValueError(f"{label}: invalid SHA-256 digest")
    return value


def _matrix(matrix):
    if not isinstance(matrix, list) or len(matrix) != 3 or any(not isinstance(r, list) or len(r) != 3 for r in matrix):
        raise ValueError("Rotation must be a 3x3 matrix")
    if any(type(v) not in (int, float) or not math.isfinite(v) for row in matrix for v in row):
        raise ValueError("Rotation must contain finite numbers, not booleans")
    m = [[float(v) for v in row] for row in matrix]
    for a in range(3):
        for b in range(3):
            dot = sum(m[a][k] * m[b][k] for k in range(3))
            if abs(dot - float(a == b)) > 1e-6:
                raise ValueError("Rotation must be orthonormal without scale or skew")
    det = (m[0][0] * (m[1][1]*m[2][2] - m[1][2]*m[2][1])
           - m[0][1] * (m[1][0]*m[2][2] - m[1][2]*m[2][0])
           + m[0][2] * (m[1][0]*m[2][1] - m[1][1]*m[2][0]))
    if abs(det - 1.) > 1e-6:
        raise ValueError("Rotation must preserve handedness; reflections prohibited")
    return m


def _read_plan(path):
    p = Path(path)
    if p.is_symlink() or not p.is_file() or not 0 < p.stat().st_size <= MAX_PLAN_BYTES:
        raise ValueError("Expected regular mapping plan up to 32 KiB")
    def unique_pairs(pairs):
        result = {}
        for k, v in pairs:
            if k in result:
                raise ValueError("Duplicate mapping JSON key")
            result[k] = v
        return result
    try:
        data = json.loads(p.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs,
                          parse_constant=lambda x: (_ for _ in ()).throw(ValueError("Non-finite JSON value")))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid mapping JSON") from exc
    return data


def validate_mapping_plan(plan, csv_report):
    """Validate a *proposal*, never independently endorse its truthfulness."""
    _exact(plan, PLAN_KEYS, "plan")
    if plan["schema_version"] != SCHEMA or plan["mapping_status"] != "proposed_unverified":
        raise ValueError("Only unverified mapping proposals supported")
    _positive_reference(plan["review_reference"], "review_reference")
    if (not isinstance(plan["source_id_declaration"], str)
        or not SOURCE_ID.fullmatch(plan["source_id_declaration"])):
        raise ValueError("Invalid source ID")
    if plan["source_id_declaration"] != csv_report["source_id_declaration"]:
        raise ValueError("Source declaration differs from CSV inspection")
    if plan["origin_declaration"] != csv_report["origin_declaration"]:
        raise ValueError("Origin declaration differs from CSV inspection")
    if plan["delimiter"] != csv_report["delimiter"]:
        raise ValueError("Delimiter mismatch")
    if _hash(plan["raw_file_sha256"], "raw_file_sha256") != csv_report["raw_file_sha256"]:
        raise ValueError("Raw file changed since mapping proposal")
    clock = _exact(plan["clock"], CLOCK_KEYS, "clock")
    idx = clock["index"]
    if type(idx) is not int or idx < 0 or idx >= csv_report["column_count"]:
        raise ValueError("Invalid clock column index")
    _hash(clock["header_sha256"], "clock header")
    if clock["header_sha256"] != csv_report["columns"][idx]["header_sha256"]:
        raise ValueError("Clock column header differs from frozen proposal")
    if clock["unit"] not in ("s", "ms", "us") or clock["time_reference"] not in ("relative_trigger", "instrument_recording_clock"):
        raise ValueError("Unsupported time units/reference")
    if csv_report["timebase"]["status"] != "STRUCTURE_ONLY" or csv_report["timebase"]["column_index"] != idx:
        raise ValueError("Sample clock not structurally qualified; gaps/jitter require review")
    groups = plan["groups"]
    if not isinstance(groups, list) or not 1 <= len(groups) <= MAX_GROUPS:
        raise ValueError("Require 1..5 physical quantity groups")
    used, roles = {idx}, set()
    for group in groups:
        _exact(group, GROUP_KEYS, "quantity group")
        q = group["quantity"]
        if not isinstance(q, str) or q not in ROLE_UNITS or q in roles:
            raise ValueError("Unsupported or duplicate physical quantity")
        roles.add(q)
        if group["source_unit"] not in ROLE_UNITS[q]:
            raise ValueError("Explicit unit inconsistent with declared quantity")
        if group["target_frame"] != TARGET[q]:
            raise ValueError("Head/neck output coordinate frame mismatch")
        _positive_reference(group["source_frame"], "source_frame")
        p1 = _positive_reference(group["measurement_point"], "measurement_point")
        p2 = _positive_reference(group["target_point"], "target_point")
        if p1 != p2:
            raise ValueError("Reference point change requires a separately reviewed rigid-body/wrench translation")
        for key in ("calibration_reference", "filter_reference", "uncertainty_reference"):
            _positive_reference(group[key], key)
        if group["gravity_policy"] not in GRAVITY:
            raise ValueError("Undeclared gravity handling")
        if q == "head_linear_acceleration" and group["gravity_policy"] == "not_applicable":
            raise ValueError("Linear acceleration requires explicit gravity policy")
        if q != "head_linear_acceleration" and group["gravity_policy"] != "not_applicable":
            raise ValueError("Gravity policy only applies to linear acceleration")
        columns = group["indices_xyz"]
        hashes = group["header_sha256_xyz"]
        if (not isinstance(columns, list) or len(columns) != 3
            or not isinstance(hashes, list) or len(hashes) != 3):
            raise ValueError("Every quantity needs three explicitly assigned axes and header hashes")
        for col, digest in zip(columns, hashes):
            if type(col) is not int or not 0 <= col < csv_report["column_count"] or col in used:
                raise ValueError("Duplicate or unavailable channel index")
            used.add(col)
            if _hash(digest, "component header") != csv_report["columns"][col]["header_sha256"]:
                raise ValueError("Frozen component header differs from CSV")
        _matrix(group["rotation_target_from_source"])
    return {"schema_version": SCHEMA, "status": "REVIEW_REQUIRED",
            "scientific_evidence_level": "S0",
            "source_id_declaration": plan["source_id_declaration"],
            "source_identity_verified": False, "mapping_approved": False,
            "data_import_authorized": False, "physical_validation": False,
            "mapped_quantities": sorted(roles),
            "column_count": csv_report["column_count"], "data_rows": csv_report["data_rows"],
            "raw_file_sha256": csv_report["raw_file_sha256"],
            "mapping_plan_sha256": hashlib.sha256(json.dumps(plan, sort_keys=True,
                      separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()).hexdigest(),
            "blockers": ["FILE_LEVEL_RIGHTS_NOT_INDEPENDENTLY_VERIFIED",
                         "SENSOR_CALIBRATION_NOT_INDEPENDENTLY_VERIFIED",
                         "SOURCE_TO_TARGET_FRAME_NOT_INDEPENDENTLY_VERIFIED",
                         "SENSOR_LOCATION_AND_LEVER_ARM_NOT_INDEPENDENTLY_VERIFIED",
                         "NO_PHYSICAL_MODEL_VALIDATION"],
            "note": "Declared transforms may be incorrect. No source permission, calibration or protection claim follows from syntactic validation."}


def _synthetic_summary(path, plan, column_count):
    """Only synthetic fixtures: aggregate SI vectors after explicit SO(3) rotation."""
    if plan["origin_declaration"] != "SYNTHETIC_HEADFORM_FIXTURE":
        return None
    # Cache validated transforms: a summary may involve hundreds of thousands of rows.
    prepared = [(g, _matrix(g["rotation_target_from_source"]),
                 ROLE_UNITS[g["quantity"]][g["source_unit"]]) for g in plan["groups"]]
    norm2sum = {g["quantity"]: 0. for g in plan["groups"]}
    peaks = {g["quantity"]: 0. for g in plan["groups"]}
    means = {g["quantity"]: [0., 0., 0.] for g in plan["groups"]}
    rows = 0
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        r = csv.reader(f, delimiter=DELIMITERS[plan["delimiter"]], strict=True)
        next(r)
        for row in r:
            rows += 1
            if len(row) != column_count:
                raise ValueError("Synthetic CSV structure changed during demonstration")
            for g, m, s in prepared:
                v = [float(row[i]) * s for i in g["indices_xyz"]]
                if not all(math.isfinite(x) for x in v):
                    raise ValueError("Nonfinite mapped synthetic measurement")
                rotated = [sum(m[j][k] * v[k] for k in range(3)) for j in range(3)]
                sq = sum(x*x for x in rotated)
                norm2sum[g["quantity"]] += sq
                peaks[g["quantity"]] = max(peaks[g["quantity"]], math.sqrt(sq))
                for j in range(3):
                    means[g["quantity"]][j] += rotated[j]
    return {name: {"peak_resultant_si": peaks[name],
                   "rms_resultant_si": math.sqrt(norm2sum[name] / rows),
                   "mean_components_target_frame_si": [v / rows for v in means[name]],
                   "units": {"head_linear_acceleration": "m/s^2",
                             "head_angular_acceleration": "rad/s^2",
                             "head_angular_velocity": "rad/s",
                             "upper_neck_force": "N", "upper_neck_moment": "N*m"}[name]}
            for name in peaks}, rows


def review_mapping(plan_path, csv_path):
    plan = _read_plan(plan_path)
    # Read raw CSV through the existing bounded structural probe; no header labels
    # or samples appear in the public report.
    clock = _exact(plan.get("clock"), CLOCK_KEYS, "clock")
    source_id = plan.get("source_id_declaration")
    origin = plan.get("origin_declaration")
    report = inspect_csv(csv_path, source_id=source_id, origin=origin,
                         delimiter=plan.get("delimiter"), time_column=clock["index"],
                         time_unit=clock["unit"])
    check = validate_mapping_plan(plan, report)
    if origin == "SYNTHETIC_HEADFORM_FIXTURE":
        # Detect changes between structural inspection and numerical demonstration.
        summary, counted_rows = _synthetic_summary(csv_path, plan, report["column_count"])
        h = hashlib.sha256()
        with Path(csv_path).open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                h.update(chunk)
        if (h.hexdigest() != report["raw_file_sha256"]
            or _safe_file(Path(csv_path)).st_size != report["raw_file_bytes"]
            or counted_rows != report["data_rows"]):
            raise ValueError("Synthetic input changed during mapping demonstration")
        check["synthetic_aggregate_demo"] = summary
    else:
        check["synthetic_aggregate_demo"] = None
    return check


def main(argv=None):
    p = argparse.ArgumentParser(description="Offline S0-only review of explicitly proposed nonhuman measurement mapping")
    p.add_argument("plan", type=Path)
    p.add_argument("csv_file", type=Path)
    p.add_argument("--out", type=Path)
    a = p.parse_args(argv)
    try:
        obj = review_mapping(a.plan, a.csv_file)
        encoded = json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n"
        if a.out is not None:
            if a.out.exists() or a.out.is_symlink() or a.out.resolve() in (a.plan.resolve(), a.csv_file.resolve()):
                raise ValueError("Report must be a new file distinct from inputs")
            with a.out.open("x", encoding="utf-8", newline="\n") as f:
                f.write(encoded)
        else:
            print(encoded, end="")
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, csv.Error) as exc:
        p.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
