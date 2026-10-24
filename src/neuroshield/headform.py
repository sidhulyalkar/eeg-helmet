"""Offline NONHUMAN headform bench file validation, not helmet certification.

This module performs structural and lineage checks ONLY. It never uploads data,
compares injury risk, validates calibration, or admits human-subject recordings.
"""
from __future__ import annotations

import csv
import json
from hashlib import sha256
from math import isfinite
from pathlib import Path
from statistics import median

from .provenance import canonical_hash

COLUMNS = (
    "time_s", "ax_m_s2", "ay_m_s2", "az_m_s2",
    "alpha_x_rad_s2", "alpha_y_rad_s2", "alpha_z_rad_s2",
    "omega_x_rad_s", "omega_y_rad_s", "omega_z_rad_s",
)
REQUIRED = {
    "schema_version", "origin", "fixture_id", "condition", "impact_location",
    "rig_id", "sensor_alias", "calibration_reference", "test_protocol",
    "coordinate_frame", "units",
}
ORIGINS = {"SYNTHETIC_HEADFORM_FIXTURE", "NONHUMAN_INSTRUMENTED_HEADFORM"}
UNITS = {
    "time": "s", "linear_acceleration": "m/s^2",
    "angular_acceleration": "rad/s^2", "angular_velocity": "rad/s",
}


def _metadata(data: object) -> dict:
    if not isinstance(data, dict) or set(data) != REQUIRED:
        raise ValueError("Headform manifest fields must match the documented schema exactly")
    if data["schema_version"] != "0.1.0" or not isinstance(data["origin"], str) or data["origin"] not in ORIGINS:
        raise ValueError("Unsupported schema or origin; human recordings are forbidden")
    if data["condition"] not in ("reference", "candidate"):
        raise ValueError("condition must be reference or candidate")
    if data["impact_location"] not in ("facemask", "frontal", "lateral", "rear", "oblique"):
        raise ValueError("Unknown impact location")
    if data["coordinate_frame"] != "right_handed_headform_body":
        raise ValueError("Must explicitly declare right_handed_headform_body frame")
    if data["units"] != UNITS:
        raise ValueError("SI units must be explicitly declared exactly")
    for field in ("fixture_id", "rig_id", "sensor_alias", "calibration_reference", "test_protocol"):
        value = data[field]
        if not isinstance(value, str) or not (1 <= len(value.strip()) <= 128) or value != value.strip():
            raise ValueError(f"{field} must be a nonempty identifier with at most 128 characters")
    return data


def validate_headform_bundle(manifest_path: str | Path, csv_path: str | Path) -> dict:
    """Read-only schema checks. Never returns raw bench traces to caller."""
    manifest = Path(manifest_path)
    samples = Path(csv_path)
    if manifest.stat().st_size > 16384:
        raise ValueError("Manifest exceeds 16 KiB limit")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    _metadata(data)
    if samples.stat().st_size > 64_000_000:
        raise ValueError("CSV exceeds 64 MB limit")
    digest = sha256(samples.read_bytes()).hexdigest()
    with samples.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(COLUMNS):
            raise ValueError("CSV columns must exactly match the headform schema")
        previous = None
        intervals = []
        count = 0
        first = None
        for count, row in enumerate(reader, 1):
            if count > 300_000:
                raise ValueError("Too many rows (300000 maximum)")
            if None in row or any(row[k] is None or not row[k].strip() for k in COLUMNS):
                raise ValueError(f"Malformed or missing data at row {count}")
            try:
                values = [float(row[k]) for k in COLUMNS]
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Non-numeric data at row {count}") from exc
            if not all(isfinite(v) for v in values):
                raise ValueError(f"Non-finite data at row {count}")
            t = values[0]
            if t < 0 or (previous is not None and t <= previous):
                raise ValueError(f"Invalid/nonmonotonic timestamp at row {count}")
            if previous is not None:
                intervals.append(t - previous)
            else:
                first = t
            previous = t
    if count < 3:
        raise ValueError("Need at least 3 time-aligned samples")
    md = median(intervals)
    gaps = sum(delta > 2.5 * md for delta in intervals)
    return {
        "schema_version": "0.1.0", "status": "STRUCTURE_ONLY_NOT_CALIBRATION",
        "source_origin": data["origin"], "nonhuman_only": True,
        "fixture_id": data["fixture_id"], "rows": count,
        "start_s": first, "end_s": previous,
        "median_interval_s": md, "max_interval_s": max(intervals),
        "possible_missing_sample_gaps": gaps,
        "csv_sha256": digest, "manifest_sha256": canonical_hash(data),
        "bundle_sha256": canonical_hash({"csv_sha256": digest, "manifest": data}),
        "warnings": [
            "Structural checks cannot establish actual sensor calibration, head coupling, or time synchronization",
            "Cannot be used for concussion classification, helmet design acceptance or injury claims",
            "No actual raw measurement samples are emitted by this validator",
        ],
    }
