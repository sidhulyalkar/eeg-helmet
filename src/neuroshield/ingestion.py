"""Schema-validation only. No real subject data is served by the demo API."""
import csv
from math import isfinite
from pathlib import Path

REQUIRED_COLUMNS = ("time_s", "head_ax_m_s2", "head_ay_m_s2", "head_az_m_s2",
                    "head_gx_rad_s", "head_gy_rad_s", "head_gz_rad_s")


def validate_kinematics_csv(path: str | Path) -> dict:
    file = Path(path)
    with file.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError("Missing or duplicate CSV headers")
        missing = set(REQUIRED_COLUMNS) - set(reader.fieldnames)
        if missing:
            raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))
        row_count, previous, dt_min, dt_max = 0, None, float("inf"), 0.0
        for row_count, row in enumerate(reader, start=1):
            if row_count > 10_000_000:
                raise ValueError("Refusing more than 10 million rows")
            try:
                values = [float(row[col]) for col in REQUIRED_COLUMNS]
            except (ValueError, TypeError, KeyError) as exc:
                raise ValueError(f"Row {row_count} has missing/non-numeric values") from exc
            if not all(isfinite(v) for v in values):
                raise ValueError(f"Row {row_count} contains non-finite values")
            t = values[0]
            if t < 0 or (previous is not None and t <= previous):
                raise ValueError(f"Row {row_count} has non-monotonic or negative timestamps")
            if previous is not None:
                dt = t - previous
                dt_min, dt_max = min(dt_min, dt), max(dt_max, dt)
            previous = t
        if row_count < 2:
            raise ValueError("Need at least 2 samples")
        return {"valid": True, "rows": row_count, "duration_s": round(previous, 6),
                "min_dt_s": round(dt_min, 8), "max_dt_s": round(dt_max, 8),
                "units": "SI", "warning": "Structural validation only; no sensor calibration or head coupling verified"}
