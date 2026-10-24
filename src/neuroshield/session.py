"""Strict, synthetic-only multimodal session interchange contract (V0.2).

Real athlete data must never enter the demo. No patient information, identity,
consent documentation, device credential, or raw recordings are persisted.
"""
from __future__ import annotations
import json
from pathlib import Path
from math import isfinite
from .provenance import canonical_hash

SUPPORTED_CHANNELS = {
    "head_linear_x": "m/s^2", "head_linear_y": "m/s^2", "head_linear_z": "m/s^2",
    "head_gyro_x": "rad/s", "head_gyro_y": "rad/s", "head_gyro_z": "rad/s",
    "torso_gyro_x": "rad/s", "torso_gyro_y": "rad/s", "torso_gyro_z": "rad/s",
    "eeg_f3": "uV", "eeg_f4": "uV", "emg_left": "uV", "emg_right": "uV",
}
MAX_SAMPLES_PER_CHANNEL = 100_000
MAX_CHANNELS = len(SUPPORTED_CHANNELS)
MAX_FILE_BYTES = 12_000_000


def validate_session(data: dict) -> dict:
    """Return small, digestible metadata; reject all unsupported data origins.

    Samples are expected to be synchronized to a *common experiment clock*.
    No sampling rate or clock drift is inferred from just an array length.
    """
    if not isinstance(data, dict) or set(data) != {"schema_version", "data_origin", "session_id", "channels"}:
        raise ValueError("Session must contain exactly schema_version, data_origin, session_id, channels")
    if data["schema_version"] != "0.2.0" or data["data_origin"] != "synthetic":
        raise ValueError("Only synthetic schema_version 0.2.0 sessions are accepted")
    sid = data["session_id"]
    if not isinstance(sid, str) or len(sid) > 64 or not sid.startswith("SYNTHETIC-") or not all(x.isalnum() or x in "-_" for x in sid):
        raise ValueError("Synthetic-only session ID required")
    channels = data["channels"]
    if not isinstance(channels, dict) or not 1 <= len(channels) <= MAX_CHANNELS:
        raise ValueError("Require 1-13 named synthetic channels")
    overview = {}
    for name, series in channels.items():
        if name not in SUPPORTED_CHANNELS:
            raise ValueError("Unknown channel or unit: " + str(name))
        if not isinstance(series, dict) or set(series) != {"unit", "time_s", "values", "quality"}:
            raise ValueError(f"Channel {name}: expected unit, time_s, values, quality")
        if series["unit"] != SUPPORTED_CHANNELS[name]:
            raise ValueError(f"Channel {name}: incorrect units")
        times, values, quality = series["time_s"], series["values"], series["quality"]
        if not all(isinstance(v, list) for v in (times, values, quality)):
            raise ValueError(f"Channel {name}: arrays required")
        if not 2 <= len(times) <= MAX_SAMPLES_PER_CHANNEL or len(values) != len(times) or len(quality) != len(times):
            raise ValueError(f"Channel {name}: sample count mismatch or limit exceeded")
        def valid_number(v):
            return not isinstance(v, bool) and isinstance(v, (float, int)) and isfinite(v)
        if not all(valid_number(v) for v in times + values + quality):
            raise ValueError(f"Channel {name}: nonfinite or nonnumeric sample")
        if times[0] < 0 or any(b <= a for a,b in zip(times, times[1:])):
            raise ValueError(f"Channel {name}: timestamps not strictly increasing")
        if any(q < 0 or q > 1 for q in quality):
            raise ValueError(f"Channel {name}: quality outside [0,1]")
        dt = [b-a for a,b in zip(times, times[1:])]
        # Flag significant timing gaps instead of silently interpolating.
        gaps = sum(delta > 2.5 * min(dt) for delta in dt)
        overview[name] = {"samples": len(times), "duration_s": round(times[-1]-times[0], 7),
                          "start_s": times[0], "end_s": times[-1],
                          "median_quality": sorted(quality)[len(quality)//2],
                          "low_quality_samples": sum(q < .5 for q in quality),
                          "timing_gaps": gaps, "unit": series["unit"]}
    return {"valid": True, "data_origin": "synthetic", "evidence_level": "S0",
            "session_id": sid, "channels": overview, "session_sha256": canonical_hash(data),
            "warning": "Structural validation only; no clock sync, hardware calibration, sensor coupling, or biological ground truth established."}


def validate_session_file(path: str | Path) -> dict:
    file = Path(path)
    if file.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("Session exceeds demo size limit")
    return validate_session(json.loads(file.read_text(encoding="utf-8")))


def synthetic_fixture() -> dict:
    """Deterministic miniature cross-modality fixture, never a human session."""
    times = [round(i*.001, 3) for i in range(100)]
    def channel(unit, scale):
        return {"unit": unit, "time_s": times,
                "values": [round(scale * (i % 13 - 6) / 10, 4) for i in range(100)],
                "quality": [0.25 if 20 <= i < 30 else 1.0 for i in range(100)]}
    return {"schema_version": "0.2.0", "data_origin": "synthetic", "session_id": "SYNTHETIC-fixture-001",
            "channels": {"head_gyro_z": channel("rad/s", 1),
                         "eeg_f3": channel("uV", 12),
                         "emg_left": channel("uV", 80)}}
