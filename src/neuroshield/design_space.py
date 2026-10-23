"""Deterministic exploratory Pareto screening of the illustrative model.

No selected candidate is a safe design or actual injury-risk improvement.
"""
from itertools import product
from .models import Parameters, SCENARIOS
from .physics import simulate

KEYS = ("peak_head_accel_g", "peak_angular_accel_rad_s2", "peak_neck_torque_proxy_nm")


def _dominates(a, b, tolerance=1e-8):
    return all(x<=y+tolerance for x,y in zip(a,b)) and any(x<y-tolerance for x,y in zip(a,b))


def sweep() -> dict:
    """Small fixed grid. Minimize worst-scene ratios across head and neck proxies."""
    baselines = {sc: simulate(sc, Parameters())["metrics"] for sc in SCENARIOS}
    records = []
    for stiffness,damping,travel,liner in product((60000.0,105000.0,155000.0),
                                                   (170.0,310.0,480.0),
                                                   (3.5,7.0),
                                                   (52000.0,65000.0)):
        p = Parameters(mount_k_n_m=stiffness,mount_c_ns_m=damping,
                       mount_travel_mm=travel,liner_k_n_m=liner,liner_c_ns_m=330.0)
        results={sc:simulate(sc,p)["metrics"] for sc in SCENARIOS}
        worst = tuple(round(max(results[sc][key]/baselines[sc][key] for sc in SCENARIOS),5)
                      for key in KEYS)
        records.append({"parameters":p.to_dict(),"worst_case_ratios":dict(zip(KEYS,worst)),
                        "mount_stop_scenarios":[sc for sc,r in results.items() if r["mount_limit_engaged"]]})
    vectors=[tuple(r["worst_case_ratios"].values()) for r in records]
    frontier=[r for i,r in enumerate(records) if not any(_dominates(v,vectors[i])
               for j,v in enumerate(vectors) if j!=i)]
    return {"source":"SYNTHETIC DESIGN EXPLORATION", "model_clinically_validated":False,
            "comparison":"Worst-case candidate/reference ratio across four toy impact scenes; >1 means worse.",
            "objective_names":KEYS,"candidate_count":len(records),"pareto_count":len(frontier),
            "pareto_frontier":frontier,
            "warning":"A Pareto design under unvalidated toy equations is not a helmet recommendation."}
