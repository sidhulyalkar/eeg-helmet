# NeuroShield V1.0: fixed-axis headform frame projection (S0)

This geometry-only stage bridges a ten-column 3D headform sensor CSV to a **predeclared signed one-axis summary**. It does **not** validate the existing toy 1D helmet model. It cannot infer headform anatomy, brain strain, cervical loads, concussion risk, helmet standards compliance or protective efficacy.

## Mathematical mapping

At each sample, measured vectors \(a_s,\alpha_s,\omega_s\) are expressed in the right-handed sensor/headform body frame. A **fixed** offset \(r_{s\to p}\) runs from the sensor to a second point on that **same rigid body**. The target point's acceleration in the source frame is

\[
a_p=a_s+\alpha_s\times r_{s\to p}+\omega_s\times(\omega_s\times r_{s\to p}).
\]

A constant proper rotation \(R_{s\to t}\), with \(R^\top R=I\) and determinant +1, maps source-frame components into a declared target frame. Signed components are projected onto a **fixed unit axis** \(u_t\): \(u_t^\top R_{s\to t} a_p\), \(u_t^\top R_{s\to t}\alpha_s\), \(u_t^\top R_{s\to t}\omega_s\). The sign is deliberately retained. This geometric relationship is valid only for rigid-body motion with a consistent body-fixed frame, accurately measured accelerations, and a physically determined lever arm.

The input contract **requires linear acceleration with gravity already removed** in the source frame. A raw accelerometer's specific force is not interchangeable with inertial linear acceleration. The implementation does not estimate attitude-varying gravity, sensor mounting pose, instrument bias, filtering, offset, clock lag, or measurement uncertainty. No coordinate axis is optimized against the data.

## Example and pinned configuration

Use the synthetic example plan, not an athlete recording:

```bash
PLAN_SHA=$(python -c 'import json; from neuroshield.provenance import canonical_hash; print(canonical_hash(json.load(open("examples/frame-projection-plan-SYNTHETIC.json"))))')
python -m neuroshield.frame_projection \
  examples/frame-projection-plan-SYNTHETIC.json \
  examples/bench-reference-SYNTHETIC-profile.json \
  examples/bench-reference-SYNTHETIC-manifest.json \
  examples/bench-reference-SYNTHETIC.csv \
  --expected-plan-sha256 "$PLAN_SHA" \
  --out ../headform-frame-projection-SYNTHETIC.json
```

The hash argument pins the JSON's canonical identity **during this invocation only**. It does not establish that the plan was registered before the experiment; a cryptographic timestamp, independent protocol registration, qualified reference laboratory, and verified calibration would be separate requirements.

The signed projection reports peak-absolute magnitude with signed value at that peak and a duration-weighted RMS over a predeclared window. It does not return raw vectors or waveforms. In particular, comparing these scalar values to the current model's 1D peak acceleration would be scientifically unjustified without a validated 3D-to-model degree-of-freedom correspondence and independently calibrated holdout data. That gate remains **BLOCKED**.

## Review checklist for future nonhuman experiments

- Document rigid headform attachment, sensor-to-target distance and orientation in independent, calibrated instrument records.
- Freeze the target axis and analysis window **before acquisition** using an externally timestamped protocol.
- Verify coordinate handedness and SI units at every interface, including gravity compensation and sensor-to-body calibration.
- Independently quantify timing synchronization and uncertainty propagation for both the displacement correction and the projected measurements.
- Use the existing paired-waveform and replicate-study gates for test design, maintaining the independent trial as the statistical unit.
- Use laboratory instrumented tests for any physical modifications. Never fit real athlete data or treat S0 as helmet acceptance.
