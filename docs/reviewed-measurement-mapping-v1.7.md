# V1.7: explicitly proposed nonhuman head/neck measurement mapping

**Evidence ceiling: S0.** This is a reproducible mapping *proposal* checker, not a calibrated converter, an equipment approval, or a helmet/injury risk predictor. It does not fetch external data, import human recordings, operate hardware, or authorize access to third-party files.

## Two deliberate modes

1. **Real nonhuman data, declared origin:** verify local file SHA-256, the selected time-column header hash, explicit time units, sample clock, signed 3-component physical quantity groups, unit compatibility, and a proper 3D rotation. The outcome remains `REVIEW_REQUIRED`, with **no numerical signal summary** and no data import authorization.
2. **Synthetic fixtures:** perform the same checks and additionally calculate a small unit/rotation demonstration containing only mean components, peak resultant and RMS resultant. These numbers are a software test of declared mathematics, not experimental findings. Real files must not be relabeled synthetic to circumvent the control.

The contract is in `src/neuroshield/schemas/measurement-mapping.schema.json`; its strict runtime validator additionally checks file/header SHA-256 identities, unique column assignments, sampling-clock gaps/jitter and a proper rotation (orthonormal 3×3 matrix, determinant +1). Values supplied by the user are **declarations** and must be independently reviewed.

## Reproducible synthetic example

```bash
python -m neuroshield.csv_probe \
  examples/measurement-mapping-SYNTHETIC.csv \
  --source-id synthetic-headform-fixture \
  --origin SYNTHETIC_HEADFORM_FIXTURE --time-column 0 --time-unit ms

python -m neuroshield.measurement_mapping \
  examples/measurement-mapping-SYNTHETIC.json \
  examples/measurement-mapping-SYNTHETIC.csv \
  --out ../mapping-review-SYNTHETIC.json
```

The fixture contains a declared *synthetic* +1 g x-axis linear-acceleration signal, a +2000 N·mm y-axis neck moment, a 90° counterclockwise rotation of the head sensor frame about z, and pre-trigger negative relative timestamps. The demonstration should yield a head linear acceleration vector mean of about `[0, 9.80665, 0]` m/s² and a neck moment resultant of 2 N·m. None of these values are actual measurements.

## Mathematical contract

Each group provides its ordered sensor vector `v_s = (x,y,z)`, a fixed unit conversion `c`, and a **proper** rotation matrix `R` from sensor axes to a declared target frame:

`v_target = R * (c * v_source)`.

The allowlisted quantities are head linear acceleration (`g`, `m/s²`), head angular acceleration (`deg/s²`, `rad/s²`), head angular velocity (`deg/s`, `rad/s`), upper-neck force (`N`, `kN`), and upper-neck moment (`N*mm`, `N*m`). All conversions are static constants, and a `g` conversion means standard gravity 9.80665 m/s², **not** an automatically subtracted gravity vector.

**Head and upper-neck are different frames**: `right_handed_headform_body` versus `right_handed_upper_neck_frame`. An axis reflection or scale/shear is invalid even if a pretty plot could be made from it. Angular quantities are axial vectors; the determinant +1 condition prevents silently applying mirror transformations.

**Reference points must remain identical** between source and target. Pure rotation of a measured acceleration at an off-center sensor does not yield acceleration at the headform center of mass. Rigid-body transport needs measured angular acceleration, angular velocity, sensor lever arm and a reviewed frame convention. Likewise, moving a moment from point P to Q needs a signed force–moment translation, **not** just a rotated moment. This V1.7 contract refuses all reference-point translations instead of guessing their sign or offset.

Filtering, gravity policy, calibration and uncertainty are explicit documentation **references**, not an approval mechanism. Missing source files, invalid/double-used axes, changed headers, invalid clock units, sample gaps/jitter, or unreviewed coordinate transformations must not be papered over by posthoc interpolation or fabricated assumptions.

## Actual Borealis source status

The [Borealis dataset](https://doi.org/10.5683/SP3/ZUZMCM) by Bailly et al. lists six e-scooter curb-collision Hybrid III sled tests, head kinematics and upper-neck force/moment signals, plus a `Crash_1.csv` and a measurement-specific `_Read_me.txt`. The repository landing page displays a CC BY 4.0 dataset license. **The actual measurement README content, CSV headers, coordinate-system convention, per-channel units, filter settings and calibration chain have not been inspected in this implementation.** No Borealis-specific plan is supplied or guessed. These tests are not football facemask impact tests.

Prior to an approved real-file mapping, a trained reviewer must preserve the precise source version, file-level legal terms, SHA-256, original column definitions, coordinate-frame basis/origin, instrumentation and clock documentation, filters/gravity handling, sensor position and uncertainty. Third-party raw measurements remain outside this Git repository and agent-accessible indexing. A mapping proposal may be useful to find deficiencies, but a passing software check remains **S0 with `mapping_approved=false`**.

## Contribution and agent integration

An external scientist can attach the *sanitized report* (after reviewing disclosure rights) and plan metadata hashes to a GitHub issue or RO-Crate, but should never publish private data, instrument serials or unrestricted raw experiment files by default. AI agents may draft questions or propose a mapping, but they cannot automatically approve it, request unrestricted local files or promote evidence. A formal reviewed dataset adapter with independent measurement calibration is a distinct future milestone. See issue #11.
