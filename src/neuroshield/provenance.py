"""Reproducibility identity, separate from actual evidence of scientific validity."""
import hashlib
import json
from importlib.resources import files


def canonical_hash(payload) -> str:
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()


def scientific_fingerprint(scenario: str, parameters: dict, scenario_detail: dict, dt: float,
                           masses: tuple, inertias: tuple) -> str:
    # Source hash ensures an equation change cannot retain the same ID.
    physics_source=files("neuroshield").joinpath("physics.py").read_text(encoding="utf-8").replace("\r\n","\n")
    source_sha=hashlib.sha256(physics_source.encode()).hexdigest()
    return canonical_hash({"model_source_sha256":source_sha,"scenario":scenario,
                           "params":parameters,"scenario_detail":scenario_detail,
                           "dt":dt,"masses":masses,"inertias":inertias})
