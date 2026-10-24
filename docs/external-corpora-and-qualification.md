# External evidence navigation and biomechanics qualification (V0.6)

> **Evidence tier: S0.** These curated cards link to external resources. They are not experimentally qualified helmet results, medical guidance for individual players, or permission to copy third-party content.

## Why three corpora?

| Namespace | Primary question | Current records |
| --- | --- | --- |
| `biomechanics` | What apparatus, models and external impact measurements could test facemask designs? | Six links to NFL, NOCSAE, Virginia Tech material |
| `neural` | What recording format, provenance, consent, coordinates and EEG channels would a future signal experiment need? | Three links to BIDS and OpenNeuro material |
| `evidence` | What distinguishes a research claim from a clinical or certification determination? | Three links to CDC, FDA and NOCSAE material |

Each record is an **authored metadata card**, with source URL, organization, version/revision hint, why the source might be useful, explicit pending license review, and `can_promote_evidence: false`. No original standards, figures, mesh files, papers, EEG waveforms, or athlete records are bundled.

### What to measure before a physical protection claim

For the first nonhuman facemask-mount experiment, define a preregistered protocol measuring at least:

1. Contact configuration and direction, approach velocity, impact location and event time origin;
2. Three-axis **headform linear acceleration and angular velocity/acceleration**, with verified sensor-to-head transform and calibration references;
3. Relevant **neck forces/moments** if the chosen instrumented apparatus can measure them, otherwise explicitly `not measured`;
4. Facemask displacement and travel-limit engagement; retention, clearance, visibility, and mechanism integrity;
5. Reference-versus-prototype matched repeat tests, including worst-case responses, uncertainty/replicate variability and adverse trade-offs;
6. Equipment test standard edition, apparatus settings and documented compliance review by a qualified laboratory.

The reduced-order V0.4 mechanical model has not yet been calibrated against these data. Never call a design 'safer' based solely on simulation. A modified football helmet cannot be treated as certified merely because its initial unmodified base was certified. Bench testing alone does not grant certification.

## Quickstart

```bash
python -m neuroshield corpora audit --root .
python -m neuroshield corpora list --root . --domain biomechanics
python -m neuroshield corpora search --root . --domain biomechanics 'non-centric impact headform rotation'
python -m neuroshield corpora gaps --root .
python -m neuroshield corpora bench --root . --out ../corpora-benchmark.json
# Requires committed, clean *catalog* files; place destination outside repository.
python -m neuroshield corpora stage --root . --out ../neuroshield-metadata-index
```

The last command writes `biomechanics/`, `neural/`, and `evidence/` subdirectories plus a Git-SHA-provenance manifest. Only committed, cataloged *titles, publisher names, URLs, revisions, and short authored relevance notes* are written. The stage operation rejects uncommitted edits and refuses to overwrite existing output. Review every staged file before any indexer is run.

Optional XERJ (installation and data behavior must be reviewed independently):

```bash
xerj autoindex ../neuroshield-metadata-index/biomechanics --prefix eeg-helmet-biomechanics
xerj autoindex ../neuroshield-metadata-index/neural --prefix eeg-helmet-neural
xerj autoindex ../neuroshield-metadata-index/evidence --prefix eeg-helmet-evidence
```

These are illustrative CLI commands and **were not executed as part of V0.6**. Verify syntax against your installed XERJ version. Do not index local `data/`, `artifacts/`, athlete recordings, full standards or extracted papers.

## Honest benchmark interpretation

`corpora bench` evaluates a fixed set of 12 short *metadata lookup* queries grouped by domain. The expected IDs are defined in `knowledge/corpora/questions.json`. They were authored with the seed catalog, so high performance is an **integration smoke test**, not independent evidence of general retrieval quality. It is not comparable to the earlier V0.5 **code navigation** benchmark.

Before adopting XERJ for larger corpora: freeze a new, independently authored question set before tuning; use identical source versions and question splits for lexical (`rg`/baseline), XERJ lexical, and semantic/hybrid; normalize rankings to unique source IDs; report Hit@5/MRR, query latency, index time/size and answer-citation accuracy. A missing executable is **NOT TESTED**, never a failure or a pass.

## License and provenance workflow

1. Retain hyperlinks and small original authored summaries only. `metadata_only` is not a reviewed license.
2. Before downloading the NFL FE toolkit, NOCSAE standard contents or other third-party files, record the **actual file-level terms** (including derivatives/commercial usage) and immutable revision/hash in a separate approval process.
3. A paper, a webpage, a GitHub repository or an XERJ hit cannot verify a helmet simulation or a medical hypothesis. External references are contextual citations, not measured model qualification.
4. File a reproducible external test with independently calibrated sensors and error metrics before considering physical model calibration. Clinical injury claims require a separate clinical research and regulatory pathway.
5. The link registry is itself code-reviewed, but this software has not independently checked URL uptime, content correctness, current standard edition, or licenses.

## What stays blocked

`python -m neuroshield corpora gaps --root .` reports the four linked hypotheses, their exact source references, missing independent validation, and the next experiment. These remain `S0` regardless of retrieval quality or numerical convergence. Do not turn research metadata into a claim of concussion prevention, individual risk prediction, FDA device status, or NOCSAE compliance.
