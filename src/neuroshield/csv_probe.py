"""Offline structural inspection of a *declared* nonhuman research CSV.

No provider-specific column guesses, signal conversion, network, raw-sample export,
permission decisions, or scientific-evidence promotion. Never a medical tool.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path
from statistics import median

SCHEMA = "neuroshield.csv-probe/0.1"
MAX_BYTES = 64_000_000
MAX_ROWS = 750_000
MAX_COLS = 256
MAX_HEADER_CHARS = 180
PREVIEW_ROWS = 128
MAX_FIELD_BYTES = 16_384
SOURCE_ID = re.compile(r"[a-z][a-z0-9-]{2,63}\Z")
DELIMITERS = {"comma": ",", "semicolon": ";", "tab": "\t"}
TIME_UNITS = {"s": 1.0, "ms": .001, "us": .000001}


def _safe_file(path: Path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("Expected a regular, nonsymlink CSV file")
    st = path.stat()
    if st.st_size == 0 or st.st_size > MAX_BYTES:
        raise ValueError("CSV empty or exceeds 64 MB limit")
    return st


def _digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inspect_csv(path: str | Path, *, source_id: str, origin: str,
                delimiter: str = "comma", time_column: int | None = None,
                time_unit: str | None = None, include_header_labels: bool = False) -> dict:
    """Read-only structural triage, never a checked calibration or input converter.

    Header positions and optional declared time column are user-reviewed; neither
    an unknown CSV dialect nor acceleration/neck channels are inferred.
    """
    if not isinstance(source_id, str) or not SOURCE_ID.fullmatch(source_id):
        raise ValueError("Invalid public source identifier")
    if origin not in ("NONHUMAN_INSTRUMENTED_HEADFORM", "SYNTHETIC_HEADFORM_FIXTURE"):
        raise ValueError("Only explicitly declared nonhuman/synthetic headform data supported")
    if delimiter not in DELIMITERS:
        raise ValueError("Choose comma, semicolon or tab delimiter")
    if (time_column is None) != (time_unit is None):
        raise ValueError("Time column and time unit must be declared together")
    if time_column is not None and (type(time_column) is not int or time_column < 0 or time_unit not in TIME_UNITS):
        raise ValueError("Invalid time-column index or time unit")
    if type(include_header_labels) is not bool:
        raise ValueError("Header-label opt-in must be Boolean")

    path = Path(path)
    before = _safe_file(path)
    digest = _digest(path)
    numeric_counts: list[int] = []
    previous = None
    intervals: list[float] = []
    first = last = None
    rows = 0
    with path.open(encoding="utf-8-sig", errors="strict", newline="") as stream:
        csv.field_size_limit(MAX_FIELD_BYTES)
        reader = csv.reader(stream, delimiter=DELIMITERS[delimiter], strict=True)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError("Missing CSV header") from exc
        if not header or len(header) > MAX_COLS or any(
            not x.strip() or len(x) > MAX_HEADER_CHARS or any(ord(ch) < 32 for ch in x)
            for x in header
        ):
            raise ValueError("Invalid or oversized CSV header")
        if len(set(header)) != len(header):
            raise ValueError("Duplicate CSV column names need manual review")
        if time_column is not None and time_column >= len(header):
            raise ValueError("Time-column index outside header range")
        numeric_counts = [0] * len(header)
        for row in reader:
            rows += 1
            if rows > MAX_ROWS:
                raise ValueError("CSV exceeds supported row limit")
            if len(row) != len(header):
                raise ValueError("Inconsistent CSV field count")
            if rows <= PREVIEW_ROWS:
                for col, value in enumerate(row):
                    try:
                        if math.isfinite(float(value)):
                            numeric_counts[col] += 1
                    except (ValueError, OverflowError):
                        pass
            if time_column is not None:
                try:
                    t = float(row[time_column]) * TIME_UNITS[time_unit]
                except (ValueError, OverflowError) as exc:
                    raise ValueError("Declared timestamp contains nonnumeric values") from exc
                if not math.isfinite(t) or t < 0 or (previous is not None and t <= previous):
                    raise ValueError("Declared timestamp must be finite, nonnegative and increasing")
                if previous is not None:
                    intervals.append(t - previous)
                else:
                    first = t
                previous = last = t
    if rows < 3:
        raise ValueError("Need at least three rows for structural review")
    after = _safe_file(path)
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
        after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
    ):
        raise ValueError("File changed while being inspected; rerun on a pinned copy")

    preview_n = min(rows, PREVIEW_ROWS)
    columns = [{"index": i,
                "header_sha256": hashlib.sha256(name.encode("utf-8")).hexdigest(),
                "numeric_preview_fraction": numeric_counts[i] / preview_n}
               for i, name in enumerate(header)]
    if include_header_labels:
        for item, name in zip(columns, header):
            item["header_label_local_opt_in"] = name
    clock = {"status": "NOT_CHECKED_NO_EXPLICIT_MAPPING"}
    if time_column is not None:
        med = median(intervals)
        gaps = sum(delta > 2.5 * med for delta in intervals)
        jitter = max(abs(dt / med - 1.0) for dt in intervals)
        clock = {"status": "POSSIBLE_GAPS_OR_JITTER" if gaps or jitter > .05 else "STRUCTURE_ONLY",
                 "column_index": time_column, "declared_input_unit": time_unit,
                 "first_time_s": first, "last_time_s": last,
                 "median_interval_s": med, "estimated_sampling_hz": 1.0 / med,
                 "possible_missing_sample_gaps": gaps,
                 "maximum_fractional_interval_deviation": jitter}
    issues = []
    if clock["status"] == "NOT_CHECKED_NO_EXPLICIT_MAPPING":
        issues.append("TIME_COLUMN_MAPPING_REQUIRED")
    elif clock["status"] == "POSSIBLE_GAPS_OR_JITTER":
        issues.append("REVIEW_SAMPLE_CLOCK_GAPS_OR_JITTER")
    return {"schema_version": SCHEMA, "status": "STRUCTURAL_REVIEW_REQUIRED",
            "scientific_evidence_level": "S0", "source_id_declaration": source_id,
            "origin_declaration": origin, "raw_file_sha256": digest,
            "raw_file_bytes": before.st_size, "data_rows": rows,
            "column_count": len(header), "delimiter": delimiter,
            "columns": columns, "timebase": clock, "structural_flags": issues,
            "source_identity_verified": False, "mapping_approved": False, "calibration_verified": False,
            "data_import_authorized": False, "physical_validation": False,
            "limitations": "File-level legal rights, source identity, instrumentation, calibration, signal units, gravity/filter conventions, and coordinate frames require independent review. No measured values are returned."}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Offline, read-only nonhuman CSV mapping and clock probe")
    p.add_argument("csv_file", type=Path)
    p.add_argument("--source-id", required=True)
    p.add_argument("--origin", required=True, choices=["NONHUMAN_INSTRUMENTED_HEADFORM", "SYNTHETIC_HEADFORM_FIXTURE"])
    p.add_argument("--delimiter", choices=sorted(DELIMITERS), default="comma")
    p.add_argument("--time-column", type=int)
    p.add_argument("--time-unit", choices=sorted(TIME_UNITS))
    p.add_argument("--include-header-labels", action="store_true",
                   help="Only locally; opt in to displaying potentially sensitive column titles")
    p.add_argument("--out", type=Path)
    a = p.parse_args(argv)
    try:
        report = inspect_csv(a.csv_file, source_id=a.source_id, origin=a.origin, delimiter=a.delimiter,
                             time_column=a.time_column, time_unit=a.time_unit,
                             include_header_labels=a.include_header_labels)
        encoded = json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n"
        if a.out is not None:
            if a.out.exists() or a.out.is_symlink() or a.out.resolve() == a.csv_file.resolve():
                raise ValueError("Output must be a new file and may not replace input")
            with a.out.open("x", encoding="utf-8", newline="\n") as f:
                f.write(encoded)
        else:
            print(encoded, end="")
    except (ValueError, OSError, csv.Error, UnicodeError) as exc:
        p.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
