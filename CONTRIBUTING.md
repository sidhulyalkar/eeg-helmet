# Contributing to NeuroShield

We welcome contributions to reproducible impact mechanics, transparent model verification, signal quality evaluation, consent architecture, accessibility and external developer experience.

**Required invariants**:

1. Never present synthetic EEG/EMG, simulated load proxies or visualization colors as medical measurements, tissue strain, concussion diagnoses or verified injury-risk reduction.
2. No personal or athlete data in tests, examples, commits, logs, CI artifacts or public API routes.
3. Document SI units, coordinate frames, uncertainties, assumptions, and reference baseline for every new numerical output.
4. Preserve separation of scientific input fingerprint from execution trace digest.
5. Every new parameter or model modification requires a deterministic regression test and, where applicable, a numerical convergence test.
6. No modifications to protective equipment or human impact testing without qualified safety partners and applicable approvals.
7. Disclose any known validation failure or adverse trade-off instead of ranking designs solely by an aggregate score.

## Local checks

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m neuroshield export --scenario oblique --out /tmp/neuroshield-example.json
```

Propose small scoped pull requests with a scientific claim/evidence statement, reproducibility instructions and explicit limitations. For code touching medical data or user identities, submit design documentation first; the current project has **no** production healthcare identity or data security.
