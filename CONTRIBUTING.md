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

## Scientific PR review template

State the research question and intended context of use, the owning workflow, exact units/frames, source rights, predeclared primary metric, negative controls and remaining evidence limits. Show any change in model predictions, failure rates or holdout results. Green software tests do **not** demonstrate protective performance.

From the repository root run:

    python -m neuroshield.research_map audit --root .
    python -m unittest discover -s tests -v

When adding a new public scientific module, update knowledge/research-workflows.json with its owner, tests and limitations. If the scope of a scientific claim changes, also update knowledge/registry.json. See docs/START_HERE.md and docs/SCIENTIFIC_ARCHITECTURE.md.


## Open EEG ecosystem contributions

For a hardware-free starting point, read the [open EEG ecosystem and global contribution plan](docs/open-eeg-ecosystem-and-community.md) and run:

    python -m neuroshield.ecosystem audit --root .
    python -m neuroshield.ecosystem list --category headwear
    python -m neuroshield.ecosystem search "electrode contact"
    python -m neuroshield.research_map show open-eeg-ecosystem

The catalog is deliberately a **reference-only index**. Before adding a resource, verify a canonical HTTPS link, document its actual openness (open software, open hardware, public platform, hosted service or community), and state one concrete reason to inspect it plus its limitations. Keep `license_review: pending_file_level`, `reuse_authorized: false`, and `evidence_role: reference_only`. A link does not grant redistribution rights or electrical/medical approval.

First contributions do not require a device: reproduce one synthetic workflow, find a misleading limitation, validate a reference card, document a failed setup, or improve readable and accessible instructions. Never include identifiable EEG, unpublished participant imagery/head scans, restricted papers, passwords, or personally identifying information in issues, pull requests, CI logs or search indexes.

Use the repository's GitHub issue templates for reproducibility problems, independent scientific questions and upstream resource nominations. See [the community conduct expectations](CODE_OF_CONDUCT.md). We have not yet established a verified private conduct-reporting channel; this remains a governance task before broad hosted community recruitment.
