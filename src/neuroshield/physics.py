"""Three-lumped-body, two-axis *illustrative* impact simulation.

A faceguard, shell and head are connected by linear spring/damper elements.
Off-center impact torques are coupled through analogous torsional elements.
This is NOT a validated skull/neck/brain finite element model, clinical risk
model, NOCSAE test, or means of selecting safe helmet components.
"""
from __future__ import annotations
from math import sin, pi, isfinite
from .models import Parameters, SCENARIOS

DT = 0.0005
TOTAL_S = 0.25
G = 9.80665
# Rounded illustrative masses/inertias, not product-specific geometry.
MASS = (0.4, 1.15, 4.6)  # facemask, shell, head (kg)
INERTIA = (0.010, 0.027, 0.018)  # kg m^2
ARM_COUPLING = 0.065  # m, approximates spring lever arm


def _pair_force(p1, v1, p2, v2, stiffness, damping, limit=None):
    delta = p1 - p2
    value = stiffness * delta + damping * (v1 - v2)
    reached = bool(limit and abs(delta) > limit)
    if reached:
        # A progressive limit stop is included so that extra travel is not free.
        value += 6.0 * stiffness * (abs(delta) - limit) * (1 if delta > 0 else -1)
    return value, reached


def simulate(scenario: str = "oblique", params: Parameters | None = None, *, dt: float = DT,
             include_audit_traces: bool = False) -> dict:
    """Solve illustrative mechanics; dt is configurable for convergence challenges.

    Numerical step-size checks do not establish physical model validity.
    """
    if isinstance(dt, bool) or not isinstance(dt, (int, float)) or not isfinite(dt) or not 0.000125 <= dt <= 0.001:
        raise ValueError("dt must be a finite step between 0.000125 and 0.001 seconds")
    steps = round(TOTAL_S / dt)
    if abs(steps * dt - TOTAL_S) > 1e-10:
        raise ValueError("dt must divide the simulation horizon exactly")
    if not isinstance(include_audit_traces, bool):
        raise ValueError("include_audit_traces must be a boolean")
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario '{scenario}'")
    p = params or Parameters()
    s = SCENARIOS[scenario]
    fc_contact = s["contact"] == "facemask"
    m, inertia = MASS, INERTIA
    # State positions and velocities for each rigid lump.
    x = [0.0] * 3
    vx = [0.0] * 3
    theta = [0.0] * 3
    omega = [0.0] * 3
    times, head_g, angular_accel, head_omega, neck_deg = [], [], [], [], []
    mount_mm, response_proxy, neck_torque_nm, input_force = [], [], [], []
    # Primary audit peaks are computed from raw state and force evaluations,
    # never from the rounded arrays used to draw the web dashboard.
    peak_unrounded = {name: 0.0 for name in (
        "peak_head_accel_g", "peak_angular_accel_rad_s2",
        "peak_head_angular_speed_rad_s", "peak_neck_torque_proxy_nm",
        "peak_mount_deflection_mm")}
    audit = {name: [] for name in (
        "time_s", "head_linear_g", "head_angular_accel_rad_s2",
        "head_omega_rad_s", "head_relative_torso_rad",
        "facemask_mount_m", "neck_torque_proxy_nm", "external_force_n")}
    max_stop = False
    energy_dissipated = 0.0
    horizon = steps + 1
    for n in range(horizon):
        t = n * dt
        peak_duration = s["duration_ms"] / 1000.0
        incoming = s["force_n"] * sin(pi * t / peak_duration) if t < peak_duration else 0.0
        moment = incoming * s["moment_arm_m"]
        # Linear faceguard-to-shell and shell-to-head couplings.
        cm, hit_stop = _pair_force(x[0], vx[0], x[1], vx[1], p.mount_k_n_m,
                                   p.mount_c_ns_m, p.mount_travel_mm / 1000.0)
        cl, _ = _pair_force(x[1], vx[1], x[2], vx[2], p.liner_k_n_m, p.liner_c_ns_m)
        # Torques use an approximate structural lever arm, not a validated 3D geometry.
        km = p.mount_k_n_m * ARM_COUPLING**2
        dm = p.mount_c_ns_m * ARM_COUPLING**2
        kl = p.liner_k_n_m * ARM_COUPLING**2
        dl = p.liner_c_ns_m * ARM_COUPLING**2
        tm, rot_stop = _pair_force(theta[0], omega[0], theta[1], omega[1], km, dm,
                                   p.mount_travel_mm / 1000.0 / ARM_COUPLING)
        tl, _ = _pair_force(theta[1], omega[1], theta[2], omega[2], kl, dl)
        # Neck/torso is treated as a fixed spring/damper anchor: intentionally simplified.
        neck_force = 1600.0 * x[2] + 45.0 * vx[2]
        neck_torque = 8.0 * theta[2] + 0.22 * omega[2]
        external_idx = 0 if fc_contact else 1
        fs = [-cm, cm - cl, cl - neck_force]
        torques = [-tm, tm - tl, tl - neck_torque]
        fs[external_idx] += incoming
        torques[external_idx] += moment
        accels = [fs[i] / m[i] for i in range(3)]
        angular_accels = [torques[i] / inertia[i] for i in range(3)]
        # Observe ALL channels at the current state t[n], BEFORE integrating
        # to t[n+1]. Angular acceleration and velocity now share the timebase.
        # The last sample is t=TOTAL_S, with no spurious extra integration.
        raw = {
            "peak_head_accel_g": accels[2] / G,
            "peak_angular_accel_rad_s2": angular_accels[2],
            "peak_head_angular_speed_rad_s": omega[2],
            "peak_neck_torque_proxy_nm": neck_torque,
            "peak_mount_deflection_mm": (x[0] - x[1]) * 1000.0,
        }
        for name, value in raw.items():
            peak_unrounded[name] = max(peak_unrounded[name], abs(value))
        if include_audit_traces:
            for name, value in {
                "time_s": t, "head_linear_g": accels[2] / G,
                "head_angular_accel_rad_s2": angular_accels[2],
                "head_omega_rad_s": omega[2],
                "head_relative_torso_rad": theta[2],
                "facemask_mount_m": x[0] - x[1],
                "neck_torque_proxy_nm": neck_torque,
                "external_force_n": incoming,
            }.items():
                audit[name].append(value)
        max_stop |= hit_stop or rot_stop
        times.append(round(t * 1000, 4))
        head_g.append(round(accels[2] / G, 4))
        angular_accel.append(round(angular_accels[2], 3))
        head_omega.append(round(omega[2], 4))
        neck_deg.append(round(theta[2] * 180 / pi, 4))
        mount_mm.append(round((x[0] - x[1]) * 1000, 4))
        neck_torque_nm.append(round(neck_torque, 4))
        input_force.append(round(incoming, 2))
        response_proxy.append(round(min(2.0, 0.55 * abs(angular_accels[2]) / 4000.0 +
                                        0.45 * abs(accels[2]) / (G * 75)), 5))
        if n < steps:
            for i in range(3):
                vx[i] += accels[i] * dt
                x[i] += vx[i] * dt
                omega[i] += angular_accels[i] * dt
                theta[i] += omega[i] * dt
            # Still only a visualization proxy, NOT an energy conservation audit.
            energy_dissipated += dt * (p.mount_c_ns_m * (vx[0] - vx[1])**2 +
                                       p.liner_c_ns_m * (vx[1] - vx[2])**2 +
                                       p.mount_c_ns_m * ARM_COUPLING**2 * (omega[0] - omega[1])**2 +
                                       p.liner_c_ns_m * ARM_COUPLING**2 * (omega[1] - omega[2])**2)
    metrics = {
        "peak_head_accel_g": round(peak_unrounded["peak_head_accel_g"], 2),
        "peak_angular_accel_rad_s2": round(peak_unrounded["peak_angular_accel_rad_s2"], 1),
        "peak_head_angular_speed_rad_s": round(peak_unrounded["peak_head_angular_speed_rad_s"], 2),
        "peak_neck_torque_proxy_nm": round(peak_unrounded["peak_neck_torque_proxy_nm"], 2),
        "peak_mount_deflection_mm": round(peak_unrounded["peak_mount_deflection_mm"], 2),
        "dissipated_energy_proxy_j": round(energy_dissipated, 2),
        "mount_limit_engaged": max_stop,
    }
    warnings = ["ILLUSTRATIVE NON-VALIDATED SIMULATION: outputs are not concussion risk, tissue strain or certification results."]
    if max_stop:
        warnings.append("Mount travel limit engaged: hard-stop behavior can increase transmitted loads.")
    if scenario in ("lateral", "rear"):
        warnings.append("Shell strike bypasses the facemask coupling in this reduced-order model.")
    from .provenance import scientific_fingerprint, canonical_hash
    parameters = p.to_dict()
    traces = {"time_ms": times, "head_linear_g": head_g, "head_angular_accel_rad_s2": angular_accel,
              "head_omega_rad_s": head_omega, "head_relative_torso_deg": neck_deg,
              "facemask_mount_mm": mount_mm, "mechanical_response_proxy": response_proxy,
              "neck_torque_proxy_nm": neck_torque_nm, "external_force_n": input_force}
    fingerprint = scientific_fingerprint(scenario, parameters, s, dt, MASS, INERTIA)
    return {
        "schema_version": "0.1.1",
        "provenance": {"source": "deterministic_synthetic_simulation", "clinically_validated": False,
                       "assumptions": "3 lumped bodies; 1 translational + 1 rotational axis; fixed torso; no brain tissue model",
                       "scientific_fingerprint": fingerprint, "execution_trace_sha256": canonical_hash(traces),
                       "sample_semantics": "pre_step_state_and_acceleration_at_time_t",
                       "audit_trace_sha256": canonical_hash(audit) if include_audit_traces else None},
        "scenario": scenario, "scenario_detail": s,
        "parameters": parameters,
        "sample_interval_ms": dt * 1000,
        "traces": traces,
        "metrics": metrics, "metrics_unrounded": peak_unrounded,
        **({"audit_traces": audit} if include_audit_traces else {}),
        "warnings": warnings,
    }
