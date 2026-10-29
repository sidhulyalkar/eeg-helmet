# NeuroShield Research Workbench

**V0.8 research workbench: local-first synthetic demonstrations, with offline-only interfaces for future nonhuman bench data. All distributed example signals remain synthetic.**

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
| `headform.py` | Strict, offline NONHUMAN headform bench metadata/CSV validator, sample-gap flags and content hashes | Structural checks only, not measured-data calibration |
| `bench_intake.py` | Optional hash-bound acquisition sidecar, local QC and paired kinematic summaries | Synthetic demonstrations, NEVER physical safety qualification |
| `waveform_qualification.py` | Preregistered local paired waveform screen, sample-clock and threshold gates | Descriptive S0 only; external model validation explicitly blocked |
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

# V0.3+ cross-integrator & energy audit, default 4 scenarios x 4 designs
python -m neuroshield qualify-independent --scenario all --out numerical-audit.json

# V0.4 full-precision primary trace; aligned t[n] state and acceleration
python -m neuroshield export-audit-trace --scenario oblique --out audit-SYNTHETIC.json

# Read-only NONHUMAN bench contract. The included sample is synthetic, not measured.
python -m neuroshield validate-headform examples/headform-SYNTHETIC-manifest.json examples/headform-SYNTHETIC.csv

# V0.7 BENCH DEMO (synthetic, not a real helmet or calibrated sensor)
python -m neuroshield inspect-bench-intake \
  examples/bench-reference-SYNTHETIC-profile.json \
  examples/bench-reference-SYNTHETIC-manifest.json \
  examples/bench-reference-SYNTHETIC.csv
# See docs/nonhuman-bench-intake-v0.7.md for paired reference/candidate command.

# V0.8 preregistered paired waveform screen (SYNTHETIC ONLY)
python -m neuroshield compare-bench-waveforms \
  examples/paired-waveform-plan-SYNTHETIC.json \
  examples/bench-reference-SYNTHETIC-profile.json \
  examples/bench-reference-SYNTHETIC-manifest.json \
  examples/bench-reference-SYNTHETIC.csv \
  examples/bench-candidate-SYNTHETIC-profile.json \
  examples/bench-candidate-SYNTHETIC-manifest.json \
  examples/bench-candidate-SYNTHETIC.csv \
  --out ../paired-waveforms-SYNTHETIC.json
python -m neuroshield model-measurement-gate --out ../model-validation-BLOCKED.json
# See docs/preregistered-waveform-screen-v0.8.md for interpretation and limits.

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

The 16-case fixture currently passes these **nonclinical mathematical tolerances**: 5% cross-solver difference, 1% reference refinement difference, 0.5% normalized energy residual and identical stop-engagement classification. Read `examples/numerical-audit-summary-SYNTHETIC.json` for per-case values; regenerate a full report via the CLI. **Passing is not S1 physical verification**. Both solvers could be consistently wrong about actual helmet dynamics. The baseline solver now computes full-precision peaks prior to presentation rounding, and each trace sample is labeled at the same pre-integration time. Optional raw numerical audit traces are available without exposing them through the demo API.

## Source layout and research contract

- [`docs/research-contract.md`](docs/research-contract.md): S0→S4 evidence ladder, numerical threshold definitions, and clinical/privacy boundaries.
- [`docs/architecture-and-next-experiments.md`](docs/architecture-and-next-experiments.md): architecture, experimental roadmap, sensors, and future neurOS integration.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`SECURITY.md`](SECURITY.md): developer practices and responsible reporting.
- [`docs/source-sha256-manifest.json`](docs/source-sha256-manifest.json): **historical V0.2 snapshot**, not a current-branch verification manifest. V0.3 audit reports separately contain hashes of the numerical source and parameter policy.

## V0.5 evidence knowledge and optional XERJ

`AGENTS.md`, `docs/knowledge-and-retrieval.md` and `knowledge/registry.json` provide a reviewed-code navigation map, an S0 evidence-boundary registry and a frozen navigation benchmark. Nothing in retrieval upgrades the scientific evidence level. **XERJ is optional** and is not a dependency.

```bash
python -m neuroshield knowledge audit --root .
python -m neuroshield knowledge stage --root . --out ../neuroshield-committed-corpus
python -m neuroshield knowledge search --stage ../neuroshield-committed-corpus "solver energy balance"
python -m neuroshield knowledge bench --root . --stage ../neuroshield-committed-corpus --out ../navigation-benchmark.json
# Optionally, after inspecting staged sources: xerj autoindex ../neuroshield-committed-corpus --prefix eeg-helmet
```

Indexing copies only a narrow allowlist of **committed** text files from `HEAD`, to a new directory outside the repository. It rejects symlinks, changed stage hashes and oversized files, and intentionally omits examples, artifacts, noncommitted files and human records. It is not a general privacy scanner: review sources before sharing. See the [knowledge and retrieval guide](docs/knowledge-and-retrieval.md).

## Next gates

1. **Physics credibility:** independently reproduced full-system analytical benchmarks, worst-case parameter sensitivity and energy accounting at all discontinuities. V0.4 fixes pre-step time alignment and precision in the primary output but not physical calibration.
2. **Bench validation:** responsibly licensed helmet/headform configurations, measured acceleration traces, force/torque calibration, cervical loading and stop-failure tests.
3. **Neural recording feasibility:** ethics-approved stationary EEG/EMG studies, rigorous contact-quality and motion-artifact analysis, device clock synchronization and informed consent.
4. **Clinical evidence:** external prospective research with appropriate specialists and independent assessment. Never infer concussion diagnosis or return-to-play clearance from synthetic kinematics.

**License:** Apache-2.0; see [`LICENSE`](LICENSE). No claims of fitness for protective use.

### V0.4 data-plane safeguards

- The browser API continues to serve **only synthetic physics and synthetic physiological signals**. `export-audit-trace` produces unrounded synthetic values offline; it is **not** an EEG/IMU stream.
- Physical rig data (if collected later) must use an offline, explicitly NONHUMAN headform bundle. `validate-headform` checks headers, SI units, monotonic clocks, finite values, possible missing samples and content hashes only. It does **not** check physical sensor calibration or certify sensor synchronization. It rejects human-origin recordings.
- See [`docs/headform-data-contract.md`](docs/headform-data-contract.md) for coordinate frame, calibration and future independent verification requirements.


## V0.6: separated external reference catalogs (research navigation only)

Three link-only corpora for biomechanics, neural recordings and evidence/qualification are tracked under `knowledge/corpora/`. They **do not** contain downloaded models, EEG, protected standards text or measured impact data. Their sources have not completed license review. See [`docs/external-corpora-and-qualification.md`](docs/external-corpora-and-qualification.md).

```bash
python -m neuroshield corpora audit --root .
python -m neuroshield corpora search --root . --domain biomechanics 'headform impact test'
python -m neuroshield corpora gaps --root .
python -m neuroshield corpora bench --root . --out ../corpora-benchmark.json
python -m neuroshield corpora stage --root . --out ../neuroshield-metadata-index
```

Staging requires committed, unmodified catalog files and writes exclusively metadata outside this repository. Optional XERJ indexing of these per-domain snapshots is an independently reviewed workflow. Citation navigation and passing metadata tests do not upgrade the unvalidated S0 helmet model.

## Agent-ready offline research tasks (V1.1 development)

`neuroshield.agent_protocol` exposes a **fixed synthetic-only** computational interface, not an autonomous laboratory or network API. It provides capability discovery, a bundled JSON Schema, source-bound deterministic results, and minimal RO-Crate 1.3 metadata.

```bash
python -m neuroshield.agent_protocol capabilities
python -m neuroshield.agent_protocol schema
python -m neuroshield.agent_protocol run examples/agent-task-SYNTHETIC.json --out ../agent-run-demo
python -m neuroshield.agent_protocol verify ../agent-run-demo
```

All research outputs remain **S0**. Artifact checksums verify local integrity, not authorship, calibration, licensing or physical validity. Agent hosts need separately governed authorization, isolation and resource control; this enables no network server, human-data ingestion or hardware actuation. See [the agent research architecture](docs/agentic-research-architecture.md).
