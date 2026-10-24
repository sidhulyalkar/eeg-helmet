"""Independently implemented RK4 reference for the synthetic three-body equations.

THIS IS A NUMERICAL CROSS-CHECK OF A TOY MODEL, NOT A SECOND PHYSICAL
VALIDATION. No clinical inference, hardware sizing or player assessment.

The solver deliberately DOES NOT call physics._pair_force or physics.simulate.
State layout: x[0:3], v[3:6], theta[6:9], omega[9:12].
"""
from __future__ import annotations
from math import sin, pi, isfinite

from .models import Parameters, SCENARIOS

# Duplicated here deliberately, so an accidental primary-model change is visible
# in cross-solver qualification. The values are *illustrative*, not calibrated.
_MASS = (0.4, 1.15, 4.6)
_INERTIA = (0.010, 0.027, 0.018)
_LEVER = 0.065
_DURATION_S = 0.25
_GRAVITY = 9.80665


def rk4_step(rhs, t: float, state: tuple[float, ...], h: float) -> tuple[float, ...]:
    """Generic explicit RK4 for independent analytical-test verification."""
    k1 = rhs(t, state)
    a = tuple(v + h * k / 2 for v, k in zip(state, k1))
    k2 = rhs(t + h / 2, a)
    b = tuple(v + h * k / 2 for v, k in zip(state, k2))
    k3 = rhs(t + h / 2, b)
    c = tuple(v + h * k for v, k in zip(state, k3))
    k4 = rhs(t + h, c)
    return tuple(v + (h / 6) * (f1 + 2*f2 + 2*f3 + f4)
                 for v, f1, f2, f3, f4 in zip(state, k1, k2, k3, k4))


def _external(t: float, scene: dict) -> float:
    window = scene["duration_ms"] / 1000
    return scene["force_n"] * sin(pi*t/window) if 0 <= t < window else 0.0


def _element(displacement: float, speed: float, k: float, c: float, stop: float | None = None):
    over = max(abs(displacement) - stop, 0.0) if stop is not None else 0.0
    f = k*displacement + c*speed
    potential = k*displacement*displacement/2
    if over:
        f += 6*k*over*(1.0 if displacement > 0 else -1.0)
        potential += 3*k*over*over
    return f, potential, c*speed*speed, bool(over)


def _evaluate(t: float, y: tuple[float, ...], p: Parameters, scene: dict):
    """Forces and power from independently expanded equations."""
    x, v, a, w = y[:3], y[3:6], y[6:9], y[9:12]
    limit = p.mount_travel_mm/1000.0
    fc, ep_fc, dc, stop_x = _element(x[0]-x[1],v[0]-v[1],p.mount_k_n_m,p.mount_c_ns_m,limit)
    sh, ep_sh, dl, _ = _element(x[1]-x[2],v[1]-v[2],p.liner_k_n_m,p.liner_c_ns_m)
    lever2 = _LEVER**2
    tc, ep_tc, dtc, stop_rot = _element(a[0]-a[1],w[0]-w[1],p.mount_k_n_m*lever2,p.mount_c_ns_m*lever2,limit/_LEVER)
    ts, ep_ts, dts, _ = _element(a[1]-a[2],w[1]-w[2],p.liner_k_n_m*lever2,p.liner_c_ns_m*lever2)
    anchor_f = 1600*x[2] + 45*v[2]
    anchor_t = 8*a[2] + .22*w[2]
    ext = _external(t, scene)
    moment = ext*scene["moment_arm_m"]
    applied = 0 if scene["contact"] == "facemask" else 1
    forces = [-fc, fc-sh, sh-anchor_f]
    torques = [-tc, tc-ts, ts-anchor_t]
    forces[applied] += ext
    torques[applied] += moment
    ax = tuple(f/m for f,m in zip(forces,_MASS))
    aa = tuple(q/j for q,j in zip(torques,_INERTIA))
    rhs = (*v, *ax, *w, *aa)
    energy = sum(.5*m*speed**2 for m,speed in zip(_MASS,v)) + sum(.5*j*rate**2 for j,rate in zip(_INERTIA,w))
    energy += ep_fc + ep_sh + ep_tc + ep_ts + .5*1600*x[2]**2 + .5*8*a[2]**2
    damping = dc+dl+dtc+dts+45*v[2]**2+.22*w[2]**2
    input_power = ext*v[applied] + moment*w[applied]
    return {"rhs":rhs,"energy_j":energy,"dissipation_w":damping,
            "input_power_w":input_power,"head_linear_g":ax[2]/_GRAVITY,
            "head_angular_accel_rad_s2":aa[2],"head_omega_rad_s":w[2],
            "neck_torque_proxy_nm":anchor_t,"facemask_mount_mm":(x[0]-x[1])*1000,
            "mount_limit_engaged":stop_x or stop_rot}


def solve_reference(scenario: str = "oblique", params: Parameters | None = None, *, dt: float = .000125) -> dict:
    if scenario not in SCENARIOS:
        raise ValueError("Unknown scenario")
    if isinstance(dt,bool) or not isinstance(dt,(int,float)) or not isfinite(dt) or not 0 < dt <= .001:
        raise ValueError("dt must be finite and within (0, 0.001]")
    steps = round(_DURATION_S/dt)
    if abs(steps*dt-_DURATION_S)>1e-10:
        raise ValueError("dt must divide 0.25 s exactly")
    p = params or Parameters()
    scene = SCENARIOS[scenario]
    state = (0.,)*12
    input_work, dissipation = 0., 0.
    max_balance_error = 0.
    peaks = {k:0.0 for k in ("peak_head_accel_g", "peak_angular_accel_rad_s2",
                            "peak_head_angular_speed_rad_s", "peak_neck_torque_proxy_nm",
                            "peak_mount_deflection_mm")}
    fields = {"head_linear_g":"peak_head_accel_g", "head_angular_accel_rad_s2":"peak_angular_accel_rad_s2",
              "head_omega_rad_s":"peak_head_angular_speed_rad_s", "neck_torque_proxy_nm":"peak_neck_torque_proxy_nm",
              "facemask_mount_mm":"peak_mount_deflection_mm"}
    stop = False
    initial = _evaluate(0.,state,p,scene)["energy_j"]
    for i in range(steps+1):
        t=i*dt
        ev = _evaluate(t,state,p,scene)
        if not all(isfinite(z) for z in state):
            raise ArithmeticError("Reference solver reached non-finite state")
        for src,dst in fields.items():
            peaks[dst] = max(peaks[dst],abs(ev[src]))
        stop = stop or ev["mount_limit_engaged"]
        balance = ev["energy_j"]-initial-input_work+dissipation
        max_balance_error=max(max_balance_error,abs(balance))
        if i == steps:
            break
        # Fresh derivations at four stages, including applied work and damping
        # quadrature. No reuse of the primary integrator's force implementation.
        k1=ev["rhs"]
        y2=tuple(y+dt*k/2 for y,k in zip(state,k1))
        e2=_evaluate(t+dt/2,y2,p,scene)
        k2=e2["rhs"]
        y3=tuple(y+dt*k/2 for y,k in zip(state,k2))
        e3=_evaluate(t+dt/2,y3,p,scene)
        k3=e3["rhs"]
        y4=tuple(y+dt*k for y,k in zip(state,k3))
        e4=_evaluate(t+dt,y4,p,scene)
        k4=e4["rhs"]
        state=tuple(y+dt/6*(f1+2*f2+2*f3+f4) for y,f1,f2,f3,f4 in zip(state,k1,k2,k3,k4))
        for key in ("input_power_w", "dissipation_w"):
            change = dt/6*(ev[key]+2*e2[key]+2*e3[key]+e4[key])
            if key == "input_power_w":input_work+=change
            else:dissipation+=change
        stop=stop or e2["mount_limit_engaged"] or e3["mount_limit_engaged"] or e4["mount_limit_engaged"]
    final=_evaluate(_DURATION_S,state,p,scene)
    residual=final["energy_j"]-initial-input_work+dissipation
    return {"method":"independent_explicit_rk4", "time_step_s":dt,
            "metrics":peaks,"energy_budget_j":{
                "initial_stored":initial,"final_stored":final["energy_j"],
                "external_work":input_work,"damping_dissipation":dissipation,
                "conservation_residual":residual,"maximum_transient_residual":max_balance_error},
            "mount_limit_engaged":stop, "model_evidence_level":"S0_UNVALIDATED_MECHANICS"}
