"""Offline, metadata-only external biomechanics intake triage.

No network, data fetching, third-party license approval or scientific evidence
promotion. Declared review flags are not independent verification.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from . import corpora

SCHEMA = "neuroshield.intake-ledger.v1"
ACCESS = {"public_files_listed", "restricted_files", "publication_only"}
FLAGS = (
    "file_license_reviewed",
    "permission_to_analyze_verified",
    "file_sha256_verified",
    "calibration_reviewed",
    "coordinate_frames_verified",
    "signal_units_verified",
    "independent_lab_reviewed",
)
REQUIRED = {"source_id", "listing_access", "dataset_scope", "limits", *FLAGS}
MAX_BYTES = 64_000
SAFE_TEXT = re.compile(r"^[^\x00-\x1f]{8,500}$")


def _unique_pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("Duplicate JSON field in source ledger")
        obj[key] = value
    return obj


def review(root: str | Path) -> dict:
    """Validate authored source citations and report unresolved review blockers."""
    root = Path(root).resolve()
    ledger_file = root / "knowledge" / "corpora" / "intake-ledger.json"
    if ledger_file.is_symlink() or not ledger_file.is_file() or ledger_file.stat().st_size > MAX_BYTES:
        raise ValueError("Missing, symlinked or oversized intake ledger")
    try:
        record = json.loads(
            ledger_file.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Non-finite JSON")),
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid intake ledger") from exc
    if not isinstance(record, dict) or set(record) != {"schema", "sources"} or record["schema"] != SCHEMA:
        raise ValueError("Invalid ledger schema")
    entries = record["sources"]
    if not isinstance(entries, list) or not 1 <= len(entries) <= 50:
        raise ValueError("Expected 1..50 source intake records")
    existing = {s["id"]: s for group in corpora.load_catalog(root).values() for s in group}
    seen, results = set(), []
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != REQUIRED:
            raise ValueError("Unexpected intake fields; no raw data, paths or permission claims")
        ident = entry["source_id"]
        if not isinstance(ident, str) or ident not in existing or existing[ident]["corpus"] != "biomechanics" or ident in seen:
            raise ValueError("Source must be unique and present in biomechanics catalog")
        seen.add(ident)
        if entry["listing_access"] not in ACCESS:
            raise ValueError("Unrecognized listing access status")
        for key in ("dataset_scope", "limits"):
            value = entry[key]
            if not isinstance(value, str) or not SAFE_TEXT.fullmatch(value):
                raise ValueError("Invalid source limitation or scope")
        if any(type(entry[flag]) is not bool for flag in FLAGS):
            raise ValueError("All review flags must be explicit booleans")
        blockers = [flag.upper() + "_MISSING" for flag in FLAGS if not entry[flag]]
        if entry["listing_access"] == "restricted_files":
            blockers.append("SOURCE_FILES_RESTRICTED")
        if entry["listing_access"] == "publication_only":
            blockers.append("NO_RAW_MEASUREMENT_DATASET")
        results.append({
            "source_id": ident,
            "status": "BLOCKED" if blockers else "REVIEW_REQUIRED",
            "blockers": blockers,
            "source_url": existing[ident]["url"],
            "scientific_evidence_level": "S0",
            "data_import_authorized": False,
        })
    return {
        "schema": SCHEMA,
        "status": "BLOCKED_EXTERNAL_QUALIFICATION" if any(r["status"] == "BLOCKED" for r in results) else "REVIEW_REQUIRED",
        "source_count": len(results),
        "sources": results,
        "scientific_evidence_level": "S0",
        "note": "Metadata assertions are not verified rights, calibration or study results. No network, downloads, imports or safety claims.",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Local S0-only external headform research source review")
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    try:
        result = review(args.root)
    except (ValueError, OSError, corpora.KnowledgeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0  # BLOCKED is a valid audited scientific finding, not a parser error.


if __name__ == "__main__":
    raise SystemExit(main())
