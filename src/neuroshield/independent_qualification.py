"""Numerical cross-check and energy audit; NEVER a helmet safety qualification."""
from __future__ import annotations
from hashlib import sha256
from importlib.resources import files
from math import isfinite
from .models import Parameters, SCENARIOS
from .physics import simulate
from .independent_solver import solve_reference
from .provenance import canonical_hash

METRICS = ("peak_head_accel_g","peak_angular_accel_rad_s2",
           "peak_head_angular_speed_rad_s","peak_neck_torque_proxy_nm",
           "peak_mount_deflection_mm")


def relative_error(a: float, b: float) -> float:
    """Symmetric relative difference: small peaks cannot pass by division by zero."""
    return abs(a-b)/max(abs(a),abs(b),1e-9)


def judge_case(comparison: dict, *, solver_tol: float, refine_tol: float, balance_tol: float) -> tuple[bool,list[str]]:
    failures=[]
    if comparison["worst_cross_solver_fraction"] > solver_tol:
        failures.append("cross_solver_disagreement")
    if comparison["worst_reference_refinement_fraction"] > refine_tol:
        failures.append("reference_not_converged")
    if comparison["energy_balance_fraction"] > balance_tol:
        failures.append("energy_balance_not_closed")
    return not failures,failures


def _sha_source(name: str) -> str:
    return sha256(files("neuroshield").joinpath(name).read_bytes().replace(b"\r\n",b"\n")).hexdigest()


def qualify_independent(scenario: str = "all", *, solver_tol: float = .05,
                        refine_tol: float = .01, balance_tol: float = .005) -> dict:
    """Compare primary semi-implicit Euler with separate RK4, + energy accounting.

    Tests baseline, proposed, maximum-stiffness/low damping, and low-stiffness/
    high-damping bounds across scenarios. All numeric thresholds are engineering
    acceptance gates for *this model*, not injury thresholds.
    """
    for name,value in (("solver_tol",solver_tol),("refine_tol",refine_tol),("balance_tol",balance_tol)):
        if isinstance(value,bool) or not isinstance(value,(float,int)) or not isfinite(value) or not 0 < value <= .25:
            raise ValueError(f"{name} must be finite in (0, 0.25]")
    if scenario != "all" and scenario not in SCENARIOS:
        raise ValueError("Unknown scenario")
    choices = SCENARIOS if scenario == "all" else (scenario,)
    designs={
        "reference":Parameters(), "suggested":Parameters.suggested(),
        "stiff_low_damping":Parameters.from_payload({"mount_k_n_m":250000,"mount_c_ns_m":20,"mount_travel_mm":1,
                                                  "liner_k_n_m":130000,"liner_c_ns_m":30}),
        "soft_high_damping":Parameters.from_payload({"mount_k_n_m":30000,"mount_c_ns_m":900,"mount_travel_mm":15,
                                                   "liner_k_n_m":25000,"liner_c_ns_m":800}),
    }
    cases=[]
    for scene in choices:
        for label,p in designs.items():
            primary=simulate(scene,p,dt=.000125)
            reference=solve_reference(scene,p,dt=.000125)
            coarse=solve_reference(scene,p,dt=.00025)
            errors={key:relative_error(primary["metrics"][key],reference["metrics"][key]) for key in METRICS}
            refinement={key:relative_error(coarse["metrics"][key],reference["metrics"][key]) for key in METRICS}
            energy=reference["energy_budget_j"]
            scale=max(abs(energy["external_work"]),abs(energy["damping_dissipation"]),
                      abs(energy["final_stored"]),1e-9)
            balance=abs(energy["conservation_residual"])/scale
            case={"scenario":scene,"design":label,"parameters":p.to_dict(),
                  "primary_method":"semi_implicit_euler", "reference_method":"independent_explicit_rk4",
                  "primary_dt_s":.000125,"reference_dt_s":.000125,"coarse_reference_dt_s":.00025,
                  "metric_comparison":{key:{"primary_rounded":primary["metrics"][key],
                                              "reference_unrounded":reference["metrics"][key],
                                              "cross_solver_fraction":errors[key],
                                              "reference_refinement_fraction":refinement[key]} for key in METRICS},
                  "worst_cross_solver_fraction":max(errors.values()),
                  "worst_reference_refinement_fraction":max(refinement.values()),
                  "energy_balance_fraction":balance,
                  "energy_budget_j":energy,
                  "primary_stop_engaged":primary["metrics"]["mount_limit_engaged"],
                  "reference_stop_engaged":reference["mount_limit_engaged"]}
            valid,reasons=judge_case(case,solver_tol=solver_tol,refine_tol=refine_tol,balance_tol=balance_tol)
            if case["primary_stop_engaged"] != case["reference_stop_engaged"]:
                valid=False
                reasons.append("stop_engagement_disagreement")
            case["status"]="PASS_NUMERICAL_ONLY" if valid else "FAIL_NUMERICAL"
            case["failure_reasons"]=reasons
            cases.append(case)
    report={"schema_version":"0.3.0","source":"SYNTHETIC_INDEPENDENT_NUMERICAL_QUALIFICATION",
            "evidence_level":"S0_UNVALIDATED_MECHANICS","scope":"numerical cross-check of same toy equations",
            "thresholds":{"cross_solver_fraction":solver_tol,"reference_refinement_fraction":refine_tol,
                          "energy_balance_fraction":balance_tol},
            "scenario_config": {key: SCENARIOS[key] for key in choices},
            "source_sha256":{"primary_physics":_sha_source("physics.py"),
                             "reference_solver":_sha_source("independent_solver.py"),
                             "model_parameters":_sha_source("models.py"),
                             "qualification_policy":_sha_source("independent_qualification.py")},
            "cases":cases,
            "case_count":len(cases),"passed":sum(c["status"]=="PASS_NUMERICAL_ONLY" for c in cases),
            "status":"PASS_NUMERICAL_ONLY" if all(c["status"]=="PASS_NUMERICAL_ONLY" for c in cases) else "FAIL_NUMERICAL",
            "limitations":["Both methods implement the same simplified unvalidated physical assumptions",
                           "Primary solver returns rounded metrics; cross-solver comparison includes rounding error",
                           "Fixed-torso, lumped-mass single-axis motion is not an instrumented headform or brain model",
                           "Numerical convergence does not establish protective benefit or concussion prediction",
                           "Impact force profile is prescribed, not a validated contact boundary condition"]}
    report["report_sha256"]=canonical_hash(report)
    return report
