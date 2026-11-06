# NeuroShield Research Workbench

**Open-source, reproducible research software for exploratory head-impact mechanics, nonhuman sensor-data methods and synthetic neural-sensing interfaces.**

**Scientific evidence: S0 only.** This is *not* a certified protective helmet, medical device, concussion detector, clinically validated model, or safe-to-install hardware design. Simulation outputs do not demonstrate injury reduction. All distributed data examples are synthetic.

[Start here for researchers](docs/START_HERE.md) · [Build an EEG research headset](docs/eeg-headwear-build-guide.md) · [CAD + XERJ toolchain](docs/cad-and-retrieval-toolchain.md) · [Scientific architecture](docs/SCIENTIFIC_ARCHITECTURE.md) · [Evidence contract](docs/research-contract.md) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md)

## Run in five minutes

Python 3.10+; no third-party runtime dependencies. From the repository root:

    python -m pip install -e .
    python -m neuroshield.research_map audit --root .
    python -m neuroshield.research_map list --root .
    python -m neuroshield qualify-independent --scenario all --out ../numerical-audit.json
    python -m unittest discover -s tests -v

The numerical audit compares independently expressed solvers of **the same assumed toy equations**. Passing demonstrates bounded computational consistency, not physical model validity. For a visual synthetic demonstration, run:

    python -m neuroshield serve

Then open http://127.0.0.1:8765. The demo binds to loopback only, does not upload human recordings and is not a medical-data application.

## First EEG headform geometry experiment (hardware-free)

Explore a **synthetic, nonwearable ellipsoid with nine symbolic markers** using only Python. The generated OpenSCAD visualization is **not an electrode montage, fabricated headset, actual head shape or safety-approved design**:

    python -m neuroshield.headform_concept examples/headform-sites-SYNTHETIC.json --out ../headform-marker-preview.scad --receipt ../headform-marker-receipt.json

The receipt records declared units, geometry bounds, source hashes, markers and explicit limitations. See the [reproducible headform marker tutorial](docs/synthetic-headform-layout-v1.md), the [EEG project landscape](docs/open-eeg-ecosystem-and-community.md), and the [hardware-first safety boundaries](docs/eeg-headwear-build-guide.md). For a curated, offline external-project catalog, run `python -m neuroshield.ecosystem list --category headwear`.

## Choose a scientific workflow

| Research question | Workflow ID | Supported mode |
| --- | --- | --- |
| What does the assumed three-body model predict? | impact-model | Synthetic simulation |
| Do integration and energy audits agree? | numerical-verification | Synthetic numerical checks |
| Which data sources deserve review? | external-source-discovery | Metadata and rights review only |
| Which open EEG projects can I learn from or contribute alongside? | open-eeg-ecosystem | Curated references only; no reuse authorization |
| Are head/neck channels and frames declared consistently? | nonhuman-measurement-contracts | Structural review; no approved physical mapping |
| How do paired motions and adverse responses compare? | bench-waveform-screen | Descriptive S0 screens |
| Can neural signal interfaces be exercised? | synthetic-neural-events | Synthetic EEG/EMG only |
| Can experiments be replayed and shared? | agent-reproduction | Bounded synthetic replay / RO-Crate |
| How can results and geometry concepts be visualized? | visualization-and-cad | Non-installable demonstration |

For example:

    python -m neuroshield.research_map show nonhuman-measurement-contracts

The **read-only** workflow map lists code owners, relevant tests, methods, related S0 claims and what is *not established*. The command does not execute the displayed example, grant data permission, change hardware, or raise the evidence level. New scientific modules must be assigned a workflow owner in CI.

## Status: what is and is not established

| Capability | Software status | Scientific limitation |
| --- | --- | --- |
| Reduced-order facemask/shell/head mechanics | Runnable, deterministic, numerical test coverage | Uncalibrated to helmets and tissue |
| Independent solver and energy accounting | Numerical cross-checks and convergence smoke tests | Shared assumptions may be wrong |
| Dataset metadata inventory and file checksums | Offline source/byte-consistency utilities | Not authentication, license clearance or calibration |
| Headform/neck measurement mappings | Pinned units/frames and structural checks | Real measurements not independently reviewed or validated |
| Multi-trial waveform comparisons | Descriptive synthetic or governed local workflows | No safety rank, cervical injury threshold or clinical inference |
| Neural EEG/EMG visualization | Synthetic signals and timing demos | No real EEG/EMG acquisition or neural biomarkers |
| Agent research tasks and reproduction | Fixed, synthetic-only tasks and replayable bundles | No autonomous laboratory, real-data permissions or human independence |

**No protective-performance, concussion-risk, injury-severity or return-to-play predictions are supported.** Nonhuman physical calibration and independent outside-researcher replication remain open research tasks.

## Repository guide

    src/neuroshield/      Scientific kernels, offline QC, provenance, synthetic UI
    tests/                Positive/negative regression and evidence-boundary checks
    examples/             Clearly synthetic and reproducible fixtures
    knowledge/            Source catalogs, S0 claim registry, research workflow map
    docs/                 Current onboarding and historical scientific protocols
    cad/                  Nonfunctional OpenSCAD study; NEVER install on helmets
    .github/workflows/    Cross-platform tests, clean-wheel and RO-Crate checks

The project remains one installable **modular Python package**, not a premature network-service collection. Its scientific modules have no required LLM, GPU, XERJ or MCP dependency. Optional agent interfaces are governed *above* the deterministic scientific kernels.

## External data and scientific evidence

Public source listings do not prove file-level reuse rights or instrument validity. Our [Borealis/EPFL source-intake guide](docs/biomechanics-source-intake-v1.5.md), [local CSV inspector](docs/local-nonhuman-csv-inspection-v1.6.md), [head/neck mapping protocol](docs/reviewed-measurement-mapping-v1.7.md), and [Dataverse inventory guide](docs/dataverse-nonhuman-intake-v1.8.md) document a path to responsibly studying **nonhuman** external measurements.

Original third-party data, calibration evidence, human EEG and athlete identities must **not** be committed or automatically indexed. Source fingerprints and schema checks do not prove protective performance. Any change in research evidence tier requires qualified, independent scientific review outside the current software gates.

## V1.10: check experimental design before computing effects

Before treating impacts as independent trials, review the declared pairing, test order, laboratory day/headform/helmet clusters, impact regimes and prespecified outcomes:

    python -m neuroshield.study_design examples/study-design-SYNTHETIC.json --out ../study-design-review.json

This **metadata-only, nonhuman matched-block** preflight refuses pooled incompatible impact conditions and warns about pseudoreplication and carryover. It does not verify randomization, compute significance, read samples or approve an experiment. See [the protocol](docs/study-design-preflight-v1.10.md).

## V1.11: check unmatched experimental conditions

When impact trials cannot defensibly be paired, use a separate **unpaired/factorial design preflight** instead of inventing reference-candidate blocks:

    python -m neuroshield.unpaired_design examples/unpaired-design-SYNTHETIC.json --out ../unpaired-review.json

This six-trial fixture is fictional, with no original measurements. The receipt preserves unacquired data, exclusions and trial failures; shows per-condition coverage; flags order, apparatus and repeated-equipment confounders; and authorizes no statistical or protective-performance inference. See [the V1.11 scientific protocol](docs/unpaired-factorial-preflight-v1.11.md).

## V1.12: can the toy model's parameters be distinguished?

Before fitting numerical parameters to headform measurements, inspect how each parameter affects modeled peaks. The [model sensitivity guide](docs/model-sensitivity-and-observables-v1.12.md) explains the deliberately **synthetic-only** diagnostic, local derivative stability and why a one-axis neck-torque proxy cannot be equated with a measured six-axis neck moment.

    python -m neuroshield.model_diagnostics --scenario all --preset default --out ../model-sensitivity-SYNTHETIC.json

This command never reads external measurements or claims that the five mechanical parameters are physically identifiable.

## Reproduce and contribute

Run the [fixed outside-researcher challenge](docs/reproduction-challenge-v1.4.md) and preserve failed attempts. The [agent-ready research architecture](docs/agentic-research-architecture.md) describes the limited safe execution interface. Computed results can be bundled with RO-Crate 1.3 metadata, but successful conformance checks do not authenticate measurements or prove scientific claims.

Read [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md) before modifying calculations, coordinate frames, data permissions or evidence contracts. The [research evidence registry](knowledge/registry.json) records explicit assumptions and unresolved limitations. See [the scientific architecture](docs/SCIENTIFIC_ARCHITECTURE.md) for verification-versus-validation rules and next experiments.

**License:** Apache-2.0. No fitness for protective, clinical or regulatory use is claimed.
