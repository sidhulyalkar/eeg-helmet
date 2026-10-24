# Research evidence and optional XERJ retrieval (V0.5)

**Research status:** S0, synthetic-only; this is an engineering navigation system, NOT a scientific authority or medical decision tool.

## Separation of responsibilities

- **`knowledge/registry.json`** is a deliberately human-maintained map connecting narrowly worded claims to local source files and their limitations. `knowledge audit` checks that references exist, kinds/IDs are consistent, and every claim stays S0. It **cannot establish scientific truth**. Physical validation and any higher evidence tier require a separate protocol, external measurements, and scientific review.
- **`knowledge/questions.json`** contains twelve frozen code-navigation questions with known file owners. It is not a test of clinical correctness.
- **`knowledge stage`** creates a frozen, inspectable snapshot of only allowlisted files already committed at `HEAD`. It excludes worktree modifications, untracked files, `.env`, `data/`, `artifacts/`, `examples/`, `knowledge/` (to avoid benchmark/registry answer leakage), `.git/`, private records, binary assets, and all nested symlinks. It records SHA-256 for each file and the Git commit. Staging is *not a redaction or DLP guarantee*. Manually inspect the snapshot before indexing or sharing it.
- **`knowledge search`** and **`knowledge bench`** are dependency-free, auditable lexical baselines for local research. Compare them with `rg` and XERJ rather than asserting one wins a priori. Results link to `file:line` and the frozen commit.
- **XERJ** is **optional**. The project does not embed an XERJ runtime, clone reference repositories, send files to remote services, or treat retrieval output as verified evidence.

## Workflow

```bash
python -m neuroshield knowledge audit --root .
# Requires a committed Git checkout; stage OUTSIDE the repository.
python -m neuroshield knowledge stage --root . --out ../neuroshield-xerj-staged
python -m neuroshield knowledge search --stage ../neuroshield-xerj-staged "energy balance numerical solver"
python -m neuroshield knowledge bench --root . --stage ../neuroshield-xerj-staged --out ../navigation-baseline.json

# Optional local XERJ install and review first, from its own documentation.
xerj autoindex ../neuroshield-xerj-staged --prefix eeg-helmet
xerj search "numerical energy balance" --prefix eeg-helmet
```

**Benchmark protocol:** run the same twelve frozen questions through local lexical, `rg` on the same committed snapshot, and XERJ lexical/semantic/hybrid modes if the installed version supports each. Normalize passage hits to *owner files*, rank at top 5, compare Hit@5 and MRR, record XERJ version, commit, configuration, namespace and duration. A previous experimental NFL Player State Engine XERJ lexical pilot underperformed `rg` on natural-language queries. That prior result does not establish current XERJ performance on NeuroShield, nor does it justify replacing simpler search. A missing XERJ binary must be reported as **NOT TESTED**, not FAILURE or PASS.

## External corpora intake

Only ingest reference material when:

1. Its source, immutable commit/DOI/version, revision age, and file-level license have been reviewed and registered.
2. Citation links and `file:line` or page reference are preserved.
3. The source has a concrete need, e.g. validated headform instrumentation standards, publicly released finite-element models, sensor interface implementations, or reproducible EEG filtering code.
4. The particular license permits the intended use. **Do not copy restricted/copyleft code** into the Apache-2.0 project; use approach-only learning when compatible with the source's terms. Do not assume standards text, NFL engineering assets or medical literature can be freely redistributed.
5. External retrieved passages remain **supporting context**, never automatically increment the S0→S4 evidence level.

Use project-local namespaces (`eeg-helmet`, `nfl-pse`, `neuros`) instead of one global index. There is no automatic cross-project leakage or merge of private records. Review any cross-project code reuse, license, attribution, compatibility and unit/frame assumptions first.

## Tests and reliability

`python -m unittest discover -s tests -v` validates registry gates, unsafe paths, snapshot boundaries, checksums and offline retrieval. GitHub CI performs registry and committed-index smoke checks. Avoid committing generated `.xerj` databases, downloaded corpora or human physiological data.
