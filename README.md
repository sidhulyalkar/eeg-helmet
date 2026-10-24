# NeuroShield Research Workbench

**V0.2: A runnable, open-source *synthetic research prototype* for exploratory football-helmet biomechanics, synchronized electrophysiology visualization, and transparent comparison of candidate mechanical designs.**

> **Not protective equipment or a medical device.** No concussion prediction, diagnosis, return-to-play decision, actual brain tissue strain or helmet certification is supported. All dashboard signals are **SYNTHETIC**, mechanics are **ILLUSTRATIVE**, and the model does not represent a real commercial helmet. Never mount the generated CAD geometry on sports equipment.

*Dashboard screenshot is included in the downloadable local release archive; run the local server for the interactive workbench.*

## NeuroSpatial Open: inverse EEG research (experimental)

The **NeuroSpatial Open** module investigates identifiable information in scalp EEG using a reproducible, **S0 SYNTHETIC** inverse-problem lab. It includes referenced lead fields, correlated reference noise, Gaussian Bayesian posteriors, resolution operators, singular spectra, null-space controls, temporal observability and 8 tests. **It does not decode thoughts, validate source locations on real heads, collect human EEG or change any helmet safety claim.**

```bash
python -m pip install -e ".[neurospatial]"
python -m neuroshield.neurospatial --out synthetic-inverse-report.json
python -m unittest discover -s tests -p test_neurospatial.py -v
```

See [inverse-modeling research contract](docs/neurospatial-open.md), [open hardware/data charter](docs/neurospatial-makers-and-data.md), and [contribution guide](docs/neurospatial-contributing.md). No real data can be sent to the existing local demo server.

## Start the interactive workbench

Python 3.10+ required, no runtime third-party dependencies.

```bash
# From the unzipped neuroshield-research/ directory:
python -m pip install -e .
python -m neuroshield serve
# Open http://127.0.0.1:8765 in a browser
```

If installing in an offline environment with setuptools already installed: `python -m pip install --no-build-isolation -e .`. Or run without installation using `PYTHONPATH=src python -m neuroshield serve` on macOS/Linux; PowerShell: `$env:PYTHONPATH='src'; python -m neuroshield serve`.

The service is bound to localhost and has **no real-data upload route**. No external JavaScript or CSS dependencies, database, API keys or athlete records are used.

## What is actually implemented?

| System | V0.1 status | Evidence status |
|---|---|---|
| Facemask/shell/head dynamic simulation (translational and rotational) | Working | S0, illustrative |
| Frontal, oblique, lateral and rear simulated impacts | Working | S0, synthetic |
| Slider-controlled mount stiffness/damping/travel and liner properties | Working | S0, parameter exploration |
| Synchronized 4-panel replay and two kinematic comparison charts | Working | S0, visualized toy model |
| Synthetic EEG + bilateral cervical EMG with motion artifact quality overlay | Working | S0, synthetic; no real EEG |
| Candidate-vs-reference mechanical metrics and hard-stop warning | Working | S0, not safety scores |
| Reproducible multi-scenario Pareto parameter sweep | Working | Toy-model exploration only |
| Local JSON export + SHA-256 scientific and execution fingerprints | Working | Deterministic reproducibility identifiers only |
| Quaternion head-to-torso kinematics + quality-aware sample alignment | Working as library | Requires real IMU calibration |
| Local CLI CSV schema validator | Working | Structural validation only |
| Parametric OpenSCAD conceptual mounting fixture source generation | Working | Visualization only, never for equipment |
| Explicit purpose/scope consent decision primitive | Unit tested | Not production authentication |
| Actual instrumented mouthguard, head-neck finite-element model, real EEG hardware | **Not implemented** | Would require device/lab work |
| Actual brain strain, concussion model, NOCSAE/NFL test certification | **Not implemented** | Not claimed |

### Dashboard workflow

1. Choose an impact location (frontal facemask, oblique facemask, lateral shell, rear shell).
2. Tune proposed faceguard/liner parameters and click **Run comparison**.
3. Use **Play**, the scrubber, or arrow keys to navigate the **same time sample** in all four panels and both charts.
4. Inspect the reference vs candidate metrics and warning list. Worsening angular acceleration is shown even if peak linear acceleration improves.
5. Download an explicitly **SYNTHETIC** JSON record for reproducibility.

All model parameters and scenarios are fixed in `src/neuroshield/models.py`; equations and masses are in `src/neuroshield/physics.py`. Each numerical run records a stable SHA-256 **scientific fingerprint** over model source and inputs, separate from a hash of its produced traces. The synthetic electrophysiology overlays in `signals.py` intentionally include motion artifacts and flagged data-quality intervals.

## V0.2 numerical qualification and multimodal session contract

This milestone adds configurable simulation time steps (0.125–1.0 ms), a four-resolution numerical-refinement check, and a strictly **synthetic-only** multimodal session interchange contract.

The refinement gate compares the five principal peak outputs between the two finest tested time steps and produces `PASS_NUMERICAL_REFINEMENT_ONLY` or `FAIL_NUMERICAL_REFINEMENT`. **A numerical PASS is not S1 physical validation**. There is still no independent solver, measured headform, calibrated neck or biological recording.

```bash
python -m neuroshield qualify --scenario oblique --out numerical-oblique.json
python -m neuroshield synthetic-session --out SYNTHETIC-session.json
python -m neuroshield validate-session SYNTHETIC-session.json
```

The session validator rejects non-synthetic origin labels, identifiable subject fields, unrecognized modalities/units, non-finite values, out-of-order timestamps, inconsistent sample lengths and illegal signal quality scores. It flags possible timing gaps. It does not establish true device clock synchronization, privacy of actual athlete data or hardware signal fidelity. **Never upload real athlete recordings to the demonstration interface.**

## Other developer commands

```bash
python -m unittest discover -s tests -v
python -m neuroshield export --scenario oblique --out synthetic-oblique.json
python -m neuroshield cad-preview --out cad/concept-mount.scad
python -m neuroshield sweep --out examples/parameter-sweep.json
python -m neuroshield validate-csv path/to/imu.csv
```

The local CSV validator expects `time_s,head_ax_m_s2,head_ay_m_s2,head_az_m_s2,head_gx_rad_s,head_gy_rad_s,head_gz_rad_s`. All values must be finite and timestamps increasing. **Validation does not upload, anonymize, diagnose or share data.**

## Code layout

```text
src/neuroshield/
  models.py       scenario catalogue + bounded versionable configuration
  physics.py      deterministic 3-lump reduced-order dynamics
  signals.py      synthetic EEG/EMG + quality gates
  analysis.py     paired baseline/candidate comparison
  kinematics.py   unit quaternions, segment-relative rotation, sample gap checks
  provenance.py   distinct SHA-256 design identity and execution trace hash
  design_space.py multi-scenario exploratory Pareto sweep
  privacy.py      explicit-purpose and per-modality consent policy primitive
  ingestion.py    local CSV structure/units validator
  cad.py          OpenSCAD view-only geometry emitter
  qualification.py  numerical step-size refinement report (S0 only)
  session.py       strictly synthetic multimodal session schema validator
  server.py       localhost-only stdlib JSON API and static host
  web/            dependency-free dashboard
  __main__.py     CLI commands
cad/              CAD caution / optional OpenSCAD output
docs/             science evidence ladder and validation gates
tests/            reproducible unit/API test suite
.github/workflows automated cross-platform test matrix
```

## Model description and known limitations

- The facemask, shell and head are modeled as three lumped masses and three inertias, connected by spring/damper pairs in **one linear** and **one angular** dimension. The torso is a fixed anchor with a passive stiffness/damper surrogate.
- Forces use a half-sine pulse with a scenario-specific duration. This is **not** a standardized NFL/NOCSAE loading configuration.
- The facemask-to-shell stop adds strongly increasing stiffness after a user-selected travel bound; it is a mathematical safeguard and warning, not an engineered retention mechanism.
- Response-visualization colors come from a weighted, normalized linear/angular acceleration proxy. **They are not simulated strain distributions.**
- Torso-relative angle and neck torque are approximations from the fixed-torso model, **not** actual cervical or spinal injuries or measurements.
- The EEG/EMG overlays are deterministic synthetic waveforms; there is no biological coupling between neural activity and the mechanical model, and quality flags are illustrative.
- Model calibration, convergence at stiff parameter boundaries, uncertainty analysis, real geometry and material response, parameter identifiability, torsional/3D coupling, injury outcomes and independent reproduction **remain future research**.

See [research contract](docs/research-contract.md) for a staged scientific qualification plan and [system architecture](docs/architecture-and-next-experiments.md) for the path from this demo to calibrated hardware and eventual neurOS integration.

## Ethics, safety and governance

The local demo allows only synthetic data. The `privacy.py` module checks a scoped consent object but is **not** a data-security implementation. No real athlete data should be served until audited identity, field-level access, encryption, informed consent, subject deletion/revocation, retention policy, and medical/operations separation are added and independently reviewed. Never use unvalidated metrics for athlete selection, concussion diagnosis or clearance.

Independent bench testing, qualified safety engineers, approvals, and compliance with relevant NOCSAE standards such as ND002 (helmets), ND081 (linear impactor protocol), and ND087 (faceguards) are prerequisites to consideration as protective equipment. [NOCSAE standards library](https://nocsae.org/football-standards/).

## Roadmap

**P1: scientific integrity.** V0.2 implements a preliminary time-step refinement report. Next: independent integrator, analytic benchmarks, energy accounting, sensitivity/uncertainty, reference tests, geometry/material validation. No clinical claims.

**P2: mechanical validation.** Properly licensed reference finite-element data, qualified lab and headform tests, neck loading and facemask/chinstrap retention, worst-case safety regressions.

**P3: actual sensor feasibility.** Separate head-coupled and helmet IMUs, synchronized torso sensors, cervical sEMG and post-impact EEG with artifact rejection and calibration.

**P4: human/clinical research.** Consent/governance, clinician-supervised outcomes, blinded longitudinal validation and neurOS dataset lineage/evaluation adapters.

## License

Apache-2.0, see [LICENSE](LICENSE). This code is for research demonstration and carries no fitness-for-purpose or injury-prevention warranty.
