"""Transparent variant comparisons. Lower mechanical outputs do NOT certify safety."""
from .physics import simulate
from .signals import add_synthetic_signals
from .models import Parameters


def comparison(scenario: str, proposed: Parameters) -> dict:
    baseline = add_synthetic_signals(simulate(scenario, Parameters()))
    candidate = add_synthetic_signals(simulate(scenario, proposed))
    deltas = {}
    for key, base in baseline["metrics"].items():
        cand = candidate["metrics"][key]
        if isinstance(base, bool):
            continue
        deltas[key] = None if not base else round((cand / base - 1) * 100, 2)
    return {"baseline": baseline, "candidate": candidate, "relative_change_pct": deltas,
            "interpretation": "Mechanical design exploration only. These changes do not establish injury prevention."}
