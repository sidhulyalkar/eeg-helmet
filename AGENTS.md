# Agent instructions: NeuroShield

Read `README.md`, `docs/research-contract.md`, and `docs/knowledge-and-retrieval.md` before changes affecting simulation, physiological signals, data or evidence.

1. **S0 remains S0:** never claim clinical concussion detection, measured tissue strain, helmet certification, injury prevention, or individual risk from synthetic experiments. Numerical gates do not promote physical evidence.
2. **Reproduce first:** run `python -m unittest discover -s tests -v`, `python -m neuroshield qualify-independent --scenario all --out <outside-repo-path>`, and `python -m neuroshield knowledge audit --root .` before code claims. Do not introduce network-dependent tests.
3. **Trace changes to evidence:** update `knowledge/registry.json` when assumptions, ownership or validation contracts change. Every claim must have supporting local code/protocol, a limitation and S0 tier. The registry is a navigation map, not a peer review.
4. **Protect human recordings:** no real athlete or identifiable EEG/EMG exports, private datasets, credentials, local artifacts or noncommitted files enter a retrieval corpus. Use `knowledge stage` for allowlisted committed sources only, inspect staged output, and keep it outside the repository.
5. **External references:** pin versions, review licenses, cite file/line, never copy restricted code or copyright standards into this Apache-2.0 project.
6. **No retrieval-based overclaim:** XERJ, `rg` and lexical baseline are optional discovery tools. All retrieved suggestions must be checked against current repository code and tests. Benchmark before making XERJ a dependency.
7. **Review increments:** preserve negative tests, physical uncertainty, benchmark regressions, and separate source freshness from proof. Prefer small PRs.

8. **External corpora:** read `docs/external-corpora-and-qualification.md` before modifying `knowledge/corpora/`; metadata-only references require manual file-level license review before import. Run `python -m neuroshield corpora audit --root .` and `python -m neuroshield corpora bench --root . --out ../corpora-benchmark.json`. Never increase evidence tier from a reference link or search hit.
