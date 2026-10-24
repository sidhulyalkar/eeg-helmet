# S0 to external physical data: NONHUMAN headform contract

**Not an equipment qualification, medical device, injury predictor, concussion classifier or certification claim.**

V0.4 defines an offline *structure-only* contract for instrumented nonhuman headform experiments. It creates an auditable boundary between wholly synthetic simulation and potential future independent laboratory measurements. No human or athlete recording is accepted by `validate-headform`, and no bench ingestion route exists in the localhost browser server.

## Files

A pair of files is mandatory: `manifest.json` plus a time-ordered `samples.csv`. The example in `examples/` is **entirely synthetic**, does not represent a calibrated transducer and must never be described as experimental evidence.

Mandatory manifest schema (all fields required, no additional fields):

```json
{
  "schema_version": "0.1.0",
  "origin": "NONHUMAN_INSTRUMENTED_HEADFORM",
  "fixture_id": "fixture-local-code",
  "condition": "reference",
  "impact_location": "facemask",
  "rig_id": "opaque-rig-code",
  "sensor_alias": "opaque-sensor-code",
  "calibration_reference": "calibration-record-id",
  "test_protocol": "written-protocol-id",
  "coordinate_frame": "right_handed_headform_body",
  "units": {
    "time": "s",
    "linear_acceleration": "m/s^2",
    "angular_acceleration": "rad/s^2",
    "angular_velocity": "rad/s"
  }
}
```

For generated fake examples use `"origin": "SYNTHETIC_HEADFORM_FIXTURE"`. No names, medical metadata, identifying information or athlete IDs should be present in either file. The validator checks that origin is an allowed *label*, not that the claim is truthful.

Exactly ten CSV columns, in this order:

```
time_s,ax_m_s2,ay_m_s2,az_m_s2,alpha_x_rad_s2,alpha_y_rad_s2,alpha_z_rad_s2,omega_x_rad_s,omega_y_rad_s,omega_z_rad_s
```

Coordinate frame is right-handed and attached to the rigid headform, not the shell or facemask. Angular velocity and angular acceleration must use radians per second / radian per second squared. Acceleration must be consistent about gravity compensation across trials: document the actual sensor signal processing, bias, filter, sensor mounting, drift and units in the independently controlled protocol referenced by `test_protocol`.

## Gate and non-gate

`python -m neuroshield validate-headform manifest.json samples.csv`

The command validates explicit header order and SI units, rejects missing values, NaN/Inf, duplicate/non-increasing times, unknown origin, and undeclared frames; reports sample span, gaps and SHA-256 content hashes. It does not display raw sample traces, upload data, overwrite inputs, or make a verdict on physical adequacy. A gap flag is a prompt for inspection, not an interpolation or a diagnosis.

It **cannot verify** calibration status, sensor-to-headform coupling, cross-device time synchronization, field orientation, impact-force pulse realism, gravitational compensation, or absence of personal information embedded in string metadata. A real measurement must undergo a separate laboratory QC review, ethics/safety review as appropriate, independent reference instrument comparison, and a formally registered impact protocol before use in mechanics fitting or comparison.

## Independent next experiments

1. Establish a closed-loop calibration chain for linear acceleration, angular rate and angular acceleration with uncertainty budgets.
2. Record trial metadata, hardware revision, sensor placement, reference rig and condition-blinded replicate identifiers outside the public raw-data archive.
3. Compare instrumented headform reference and candidate configurations using repeatable impact angles and energies, explicitly report worst-case regressions in linear and rotational response.
4. Quantify cross-axis coordinate transforms, uncertainty bands, synchronization offsets, sensor saturation, missing samples, and model residuals before attempting any physical parameter estimation.
5. Treat all protective claims as **unproven** until independent certification and appropriate evidence are available. NOCSAE-standard compliance is not conferred by this repository.
