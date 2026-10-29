# V1.3 external reproduction and research bundle portability

**Purpose:** A new contributor must be able to install a distribution artifact outside the source checkout, reproduce a synthetic task, and validate its metadata without trusting the agent's prose. The software remains **S0** and does not authorize physical equipment or human recordings.

## Wheel-only release smoke test

```bash
python scripts/smoke_installed_wheel.py
```

This creates a temporary clean Python virtual environment, builds a distributable wheel, installs it with `--no-index --no-deps`, then checks package metadata, packaged JSON Schema, the bundled synthetic task runner, integrity verification and independent replay. Its build step can need network access for build dependencies, and its results do **not** establish a third-party reproduction by a different scientist.

## RO-Crate 1.3 improvements

The root dataset includes the required `datePublished` (UTC export date). This field is **publication metadata**, not part of the deterministic scientific task/result fingerprints. New bundles use a `/0.2` checksum manifest covering `task.json`, `result.json`, and `ro-crate-metadata.json`. Older `/0.1` bundles can still be read and verified, with their original V1.1 limitations.

All checksums are locally editable and therefore **not signatures** or a way to establish authenticity. The replay command is a separate computation check; passing it does not validate physical models or real-world helmet protection. RO-Crate conformance must be checked with an independent validator before claiming conformance.

Optional standalone external validator (do not mix its dependency into the runtime):

```bash
python -m pip install roc-validator==0.12.2
rocrate-validator validate ../portable-research-bundle
```

Validate the **bundle directory**, not a detached copy of its metadata file. The validator is a third-party package; any CI pass should identify its version, settings and exact run.

## External researcher acceptance task

1. Use a fresh environment and a pinned Git commit; record OS, Python, install errors and package version.
2. Run the wheel smoke test, then generate and replay both synthetic tasks with the installed wheel.
3. Preserve any mismatch and its full error output; do not quietly adjust the scientific parameters or thresholds.
4. Run an independent RO-Crate validator on a generated attached bundle.
5. Return a short reproduction report with hashes and blockers, even when it **fails**.

This is a reproducibility challenge, not a clinical validation experiment. Independent calibrated nonhuman biomechanics evidence is still missing.
