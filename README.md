# NeuroShield Research Workbench

**V0.3: an open-source, local-first, entirely synthetic biomechanics and electrophysiology research demonstration.**

> **Safety and scientific scope:** This is **not a medical device, protective helmet design, concussion detector, brain-strain estimator, or certification test**. Never install the concept CAD on protective equipment. No real athlete data are accepted by the demo server. There is no headform calibration, injury model, NOCSAE/NFL testing, or evidence of concussion reduction. All reported mechanics remain S0, unvalidated.

## Run locally

Python 3.10+, no third-party runtime dependencies:

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m neuroshield serve
# Open http://127.0.0.1:8765
```

For offline development with setuptools installed, try `python -m pip install --no-build-isolation -e .`; on macOS/Linux you can skip installation with `PYTHONPATH=src python -m neuroshield serve`. On Windows PowerShell: `$env:PYTHONPATH='src'; python -m neuroshield serve`.

The service binds to loopback only. There is no real-data upload API, user account system, database or remote telemetry. Privacy policy primitives are educational and **not** production authorization or medical-record security.

## Workbench capabilities

| Module | What it does | Evidence |
|---|---|---|
| `physics.py` | Three-body facemask/shell/head, two-axis, spring/damper/stop impact model | Synthetic toy mechanics |
| `analysis.py` / `web/` | Four-panel synchronized replay with comparative metrics, force timeline and synthetic EEG/EMG | Visualization only |
| `models.py` | Four controlled synthetic collision scenarios, bounded stiffness/damping/travel | Not product-specific |
| `design_space.py` | Multi-scenario Pareto parameter exploration that retains worsening responses | Not a helmet safety ranking |
| `qualification.py` | Four-step-size peak-metric refinement | Partial numerical check |
| `independent_solver.py` | Separately expressed RK4 solver with conservative spring/stop energy, damping and applied work | Same unvalidated physical assumptions |
| `independent_qualification.py` | 16-case cross-solver, RK4 refinement and energy-balance audit with strict numerical gates | **Numerical-only** PASS/FAIL |
| `kinematics.py` | Quaternion head-to-torso orientation and gap-aware interpolation | Not calibrated to sensors |
| `session.py` / `ingestion.py` | Synthetic-only session data contract and local CSV shape/unit validator | No actual acquisition |
| `privacy.py` | Basic purpose/scope consent decision checks | Not production-grade access control |
| `cad.py` | Nonfunctional OpenSCAD geometry concept | **NEVER INSTALL** on equipment |

**No real EEG/EMG or IMU acquisition, cervical injury criterion, finite-element brain strain, concussion prediction, athlete-specific risk estimate or validated helmet design is implemented.**

## Reproducible experiments

```bash
# Synthetic helmet comparison and multi-design exploration
python -m neuroshield export --scenario oblique --out synthetic-oblique.json
python -m neuroshield sweep --out pareto-SYNTHETIC.json

# Historical V0.2 single-integrator refinement test
python -m neuroshield qualify --scenario oblique --out numerical-oblique.json

# V0.3 cross-integrator & energy audit, default 4 scenarios x 4 designs
python -m neuroshield qualify-independent --scenario all --out numerical-audit.json

# Synthetic-only session interchange
python -m neuroshield synthetic-session --out session-SYNTHETIC.json
python -m neuroshield validate-session session-SYNTHETIC.json

# Shape and unit validation on a *local* CSV; does not anonymize or authorize sharing
python -m neuroshield validate-csv examples/kinematics-SYNTHETIC.csv

# Geometry illustration, not a buildable helmet component
python -m neuroshield cad-preview --out concept-preview.scad
```

### What numerical qualification means

The independent check compares an original semi-implicit Euler implementation with a separately written RK4 integrator **of the same toy equations**. It checks maximum symmetric peak-metric discrepancy, RK4 refinement between 0.25 and 0.125 ms, mechanical energy balance and agreement on mount-stop engagement. Cases fail the command when a threshold is exceeded. CI exercises all 16 combinations on Linux, Windows and macOS.

The 16-case fixture currently passes these **nonclinical mathematical tolerances**: 5% cross-solver difference, 1% reference refinement difference, 0.5% normalized energy residual and identical stop-engagement classification. Read `examples/numerical-audit-summary-SYNTHETIC.json` for per-case values; regenerate a full report via the CLI. **Passing is not S1 physical verification**. Both solvers could be consistently wrong about actual helmet dynamics. The baseline solver also rounds peak observables; this precision limitation is reported rather than hidden.

## Source layout and research contract

- [`docs/research-contract.md`](docs/research-contract.md): S0→S4 evidence ladder, numerical threshold definitions, and clinical/privacy boundaries.
- [`docs/architecture-and-next-experiments.md`](docs/architecture-and-next-experiments.md): architecture, experimental roadmap, sensors, and future neurOS integration.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`SECURITY.md`](SECURITY.md): developer practices and responsible reporting.
- [`docs/source-sha256-manifest.json`](docs/source-sha256-manifest.json): **historical V0.2 snapshot**, not a current-branch verification manifest. V0.3 audit reports separately contain hashes of the numerical source and parameter policy.

## Next gates

1. **Physics credibility:** unrounded and time-aligned primary observables, independently reproduced full-system benchmarks, parameter sensitivity and energy accounting for all discontinuities.
2. **Bench validation:** responsibly licensed helmet/headform configurations, measured acceleration traces, force/torque calibration, cervical loading and stop-failure tests.
3. **Neural recording feasibility:** ethics-approved stationary EEG/EMG studies, rigorous contact-quality and motion-artifact analysis, device clock synchronization and informed consent.
4. **Clinical evidence:** external prospective research with appropriate specialists and independent assessment. Never infer concussion diagnosis or return-to-play clearance from synthetic kinematics.

**License:** Apache-2.0; see [`LICENSE`](LICENSE). No claims of fitness for protective use.