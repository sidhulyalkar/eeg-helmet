# NeuroShield research platform: engineering architecture and next experimental gates

**Current status:** V0.3 is a deterministic, non-clinical research demonstration. There is no approved hardware, recorded EEG, biomechanical truth, patient or athlete database, or clinical model.

## Module graph

```text
Local synthetic laboratory workbench (implemented)

models.py (versioned parameters and scenarios)
   |                  kinematics.py (quaternions + gap-aware scalar alignment)
   v                           |
physics.py                     | (standalone library)
   |                           |
   +--> signals.py             |
   |         |                 |
   +--> analysis.py <-----------+
   |         |
   |     server.py  (/api/config and /api/compare, synthetic only)
   |         |
   |       web/ (four synchronized panels + comparison timelines)
   |
   +--> provenance.py (scientific fingerprint vs trace digest)
   +--> design_space.py (multi-scenario, nonvalidated Pareto grid)
   +--> independent_solver.py (separately implemented toy-model RK4 reference)
   +--> independent_qualification.py (16-case cross-check + energy ledger)
   +--> cad.py (unusable geometry-study OpenSCAD output)

Future, NOT implemented: physical sensors -> acquisition -> device clock alignment
-> consent-aware storage -> calibrated biomechanics -> neurOS evaluation adapter
-> blinded external comparison -> regulated/clinical study
```

## Event manifest contract proposal (not yet deployed)

```json
{
  "schema_version": "1.0.0-proposal",
  "origin": "real_or_synthetic",
  "session_pseudonym": "not-an-athlete-name",
  "consent_reference": "scope-limited identifier, not a token",
  "experiment_id": "test configuration ID",
  "timebase": "sensor hardware clock and offset/drift estimates",
  "streams": [
    {"modality": "mouthguard_imu", "units": "m/s2 and rad/s", "calibration_id": "..."},
    {"modality": "torso_imu", "units": "m/s2 and rad/s", "calibration_id": "..."},
    {"modality": "cervical_emg", "units": "V", "calibration_id": "..."},
    {"modality": "scalp_eeg", "units": "V", "calibration_id": "..."}
  ],
  "analysis_artifacts": [],
  "validation_evidence": "none"
}
```

The schema is a conceptual interface, not a supported parser. Hardware timestamps, clock drift, sensor-frame orientation, units and calibration must be retained rather than replaced by convenience-normalized arrays. **No concussion or brain injury label should ever be inferred from kinematics as if it were ground truth.**

## Work packages

### WP1: trustworthy mechanics

- Independently implement one spring/damper analytic benchmark (mass-spring impulse response).
- Test convergence with 0.25 ms, 0.5 ms and 1 ms integrators; document convergence failures at hard stops.
- Audit energy input, stored energy and dissipation; identify nonphysical parameter regions.
- Add helmet/facemask geometry under explicit coordinate frames and calibrated material curves.
- Use public finite-element assets only after verifying access and licenses; compare full reference impact traces, not only maxima.
- Sample realistic uncertainty around headform, chinstrap tension, facemask mounts, temperatures and impact positions. Every candidate must be checked for regressions.

**Success criterion:** reproducible baseline against independent headform measurements with uncertainty and all neck loading deviations reported.

### WP2: distributed sensors

- Primary head reference: instrumented mouthguard with confirmed tooth coupling and calibration, in addition to shell IMU.
- Torso reference: sternal or upper back IMU rigidly affixed and sensor-frame alignment calibration.
- Bilateral cervical sEMG: feasible pickup locations, electrode contact, sweat, motion artifacts and neck motion assessment.
- EEG: start in a stationary/post-impact feasibility mode, require clinician and ethics review for athlete monitoring; contact quality, artifact rejection, task-state matching.
- Use shared hardware synchronization pulses when available; characterize transport latency and drift independently; never interpolate over long gaps silently.

**Success criterion:** compare against calibrated lab reference instruments; meet prespecified alignment, dropout and repeatability limits.

### WP3: evidence-first replay/annotation

- Video synchronization and independent impact-site annotation.
- Show actual contact location and recorded kinematics once data exist, marked by device calibration and sampling quality.
- Display signal-quality masks even when they invalidate an entire EEG interval.
- Add blinded annotation adjudication and quality provenance to all result tables.
- Brain-strain visualization only after independently validated finite-element simulation with boundary conditions matched to the physical experiment; current visualization remains a unitless proxy.

**Success criterion:** external users can reproduce every figure from versioned data + configs, including failures and excluded windows.

### WP4: governance and independent clinical research

- Research consent built into dataset manifest and enforced with an audited identity provider, ACLs and cryptographic storage.
- Athlete controls medical/research sharing; operational team viewers never get neural data or implicit clearance status.
- Consent revocation, retention, deletion and immutable access/audit logs are specified before data capture.
- Distinguish observational association, mechanically validated improvement, and prospectively validated clinical benefit.

**Success criterion:** independent IRB/legal/security review before real subject recordings or any deployment.

## NFL / certification boundary

Actual protective-equipment experiments require appropriate engineering supervision and independent laboratory equipment. NOCSAE ND002, ND081 and ND087 are relevant baseline standards; this project does not test to or satisfy them. An off-the-shelf certified helmet cannot be presumed certified after adding a modified faceguard mount, liner, electrode or external sensor system.

## Scope of the present release

Supported: repeatable API, synthetic replay, quality-gated mock signals, comparative mechanical metrics, provenance hashes, local numeric import validation, basic quaternion math, conceptual CAD view, Pareto parameter sweep and CI.

Not supported: calibrated FE physics, validated neck injury metrics, proper electrical acquisition, clinically interpreted EEG, actual tissue strain, data privacy infrastructure for PHI, or sport participation approval.
