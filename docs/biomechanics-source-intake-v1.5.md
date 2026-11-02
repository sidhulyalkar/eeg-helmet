# Biomechanics external source intake ledger (V1.5)

**Research status: S0, metadata-only.** The ledger is a discovery and human-review queue, not a file downloader, license approval, clinical model, or helmet certification process. These links were inspected as source *landing pages*, not as independent laboratory calibration attestations.

## Ranked intake candidates

| Source | What is actually visible | Why it could help | Current blocker |
| --- | --- | --- | --- |
| [Borealis E-scooter head and neck data](https://doi.org/10.5683/SP3/ZUZMCM), 2024 | Deposited V1 dataset describes six Hybrid III sled crash tests and lists individual public measurement CSVs; landing page declares CC BY 4.0 | Head linear/rotational accelerations and upper-neck force/moment are relevant to a data ingest *method* test | File-level terms, channel labels, sampling/filtering, calibration chain and coordinate frames require inspection. E-scooter impacts are not football facemask tests |
| [EPFL hockey helmet IMU / headform data](https://zenodo.org/records/22092814), 2026 | Public Zenodo metadata and DOI 10.5281/zenodo.22092814; *files restricted* | Side-by-side helmet-mounted IMU and Hybrid III headform signals could challenge sensor-coupling assumptions | Obtain permission from depositors; no automatic access, copying or redistribution |
| [Virginia Tech Cranium Resonance Index](https://vtechworks.lib.vt.edu/items/81a61d1e-8222-49b0-8c11-f1dd86e8a46b), 2026 | Published technical note on high-frequency headform vibration, 300–3000 Hz filtering | A candidate measurement methodology when appropriately instrumented | Experimental metric, **not a finalized injury criterion**; no validated raw dataset or protective interpretation imported |

The direct [NOCSAE ND087 faceguard page](https://nocsae.org/standard-method-of-impact-test-and-performance-requirements-for-football-faceguards/) supersedes a previously indirect catalog link. Edition/revision checks and laboratory review remain mandatory. NOCSAE standards and specific source documents are not redistributed here.

## Query the source readiness ledger

```sh
python -m neuroshield corpora audit --root .
python -m neuroshield corpora search --root . --domain biomechanics "Hybrid III head neck data"
python -m neuroshield.source_intake --root .
```

The JSON ledger at `knowledge/corpora/intake-ledger.json` is linked to known source IDs in the domain catalog. The offline validator rejects unregistered source IDs, unknown fields, source paths, raw data, duplicate records and misleading evidence-tier fields. An agent can inspect which verification requirements remain unanswered, but no agent action can download or approve data from these records.

Even if *all* review flags are set to true, a source becomes `REVIEW_REQUIRED`, never `ACCEPTED` or a higher evidence tier. Those flags are **self-declared metadata**, not verified certifications. Dataset reuse requires a documented human license review and scientific audit outside this system. All public metadata cards retain `license_status: pending_manual_review`.

## Actual nonhuman dataset acceptance procedure

1. **Permissions first:** cite the actual file name, dataset version, depositor terms and intended transformations; collect a dated permission record when needed, separate from this public repository.
2. **Acquire locally only:** use the provider's authorized method, outside Git; compute SHA-256 of the exact bytes. Never import athlete recordings, identifying human data, or protected files into the agent index.
3. **Inspect physics:** verify instrumentation, SI units, sensor frame, time origin, filtering, sample rate, saturation, bias and calibration evidence. Review neck-load channel polarity and moment reference point if present.
4. **Preregister a narrow question:** e.g. can NeuroShield faithfully identify and compare the correct headform channels? Keep this separate from checking whether its 1D model predicts the recorded physics.
5. **Preserve every failure:** distinguish incompatible apparatus, insufficient methods, missed signals, and measured regressions. Publish limitations and uncertainty, not just attractive peak numbers.
6. **Only then plan a model challenge:** establish an appropriate 3D-to-1D mapping and a fixed holdout dataset; validate against independent nonhuman laboratory experiments. Current synthetic helmet outputs remain S0.

**Especially important:** Six e-scooter crash tests with several configurations are not six interchangeable replicates of one football impact. Do not pool them as independent repetitions or infer facemask performance from bicycle helmets.

## Why this belongs in an agent-ready research repo

Dataset discovery and eligibility should be machine-readable, but **the source of authority must be upstream evidence**. An LLM can propose what to inspect and cite why, but a human reviewer must verify license, provenance, and the meaning of each measurement. This ledger is deliberately not an automatic import pipeline.
