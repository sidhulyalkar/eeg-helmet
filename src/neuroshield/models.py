"""Explicit numerical contracts and guardrails for the illustrative impact model."""
from __future__ import annotations
from dataclasses import dataclass, asdict, replace
from math import isfinite


SCENARIOS = {
    "facemask": {"label": "Facemask · frontal", "force_n": 2600.0, "duration_ms": 15.0, "moment_arm_m": 0.045, "angle_deg": 20, "contact": "facemask"},
    "oblique": {"label": "Facemask · oblique", "force_n": 2300.0, "duration_ms": 13.0, "moment_arm_m": 0.105, "angle_deg": 48, "contact": "facemask"},
    "lateral": {"label": "Shell · lateral", "force_n": 2100.0, "duration_ms": 12.0, "moment_arm_m": 0.120, "angle_deg": 95, "contact": "shell"},
    "rear": {"label": "Shell · rear", "force_n": 2350.0, "duration_ms": 14.0, "moment_arm_m": -0.065, "angle_deg": 170, "contact": "shell"},
}


@dataclass(frozen=True)
class Parameters:
    """Not calibrated to a real helmet. Bounds ensure stable demo runs only."""
    mount_k_n_m: float = 155000.0
    mount_c_ns_m: float = 170.0
    mount_travel_mm: float = 3.5
    liner_k_n_m: float = 65000.0
    liner_c_ns_m: float = 280.0

    @classmethod
    def suggested(cls) -> "Parameters":
        return cls(mount_k_n_m=70000, mount_c_ns_m=310, mount_travel_mm=7.0, liner_k_n_m=52000, liner_c_ns_m=330)

    @classmethod
    def from_payload(cls, value: dict | None) -> "Parameters":
        if value is None:
            return cls()
        if not isinstance(value, dict):
            raise ValueError("parameters must be an object")
        names = set(cls.__dataclass_fields__)
        if set(value) - names:
            raise ValueError(f"Unknown parameters: {', '.join(sorted(set(value) - names))}")
        values = {}
        bounds = {
            "mount_k_n_m": (30000, 250000),
            "mount_c_ns_m": (20, 900),
            "mount_travel_mm": (1, 15),
            "liner_k_n_m": (25000, 130000),
            "liner_c_ns_m": (30, 800),
        }
        for key, entry in value.items():
            if isinstance(entry, bool) or not isinstance(entry, (int, float)) or not isfinite(entry):
                raise ValueError(f"{key} must be a finite number")
            lo, hi = bounds[key]
            if not lo <= entry <= hi:
                raise ValueError(f"{key} must be within [{lo}, {hi}]")
            values[key] = float(entry)
        return replace(cls(), **values)

    def to_dict(self):
        return asdict(self)
