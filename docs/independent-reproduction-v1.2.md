# Independent synthetic research reproduction (V1.2)

This challenge can be attempted by an outside scientist or a constrained research agent. **It has not yet been completed by an external researcher.** No helmet-safety, injury, clinical, calibration or physical-validation claim follows from completing it.

## Reproduce a pinned computation

1. Clone `https://github.com/sidhulyalkar/eeg-helmet` and record `git rev-parse HEAD` and `python --version`. Choose a fixed commit rather than a moving branch for a published comparison.
2. Install the package on an isolated machine or environment using `python -m pip install -e .`. No EEG, athlete data, third-party models, XERJ, cloud account or network service is needed after source checkout and installation.
3. Create an output **outside the repository**:

   ```shell
   python -m neuroshield.agent_protocol run examples/agent-task-SYNTHETIC.json --out ../research-run
   python -m neuroshield.agent_protocol verify ../research-run
   python -m neuroshield.reproduction ../research-run --out ../research-replay.json
   ```

4. Repeat with `examples/agent-task-numerical-SYNTHETIC.json`, using a different output path.
5. Inspect `task.json`, `result.json`, `checksums.json`, `ro-crate-metadata.json` and `research-replay.json`. Report the pinned commit, OS, Python version, task SHA-256, result SHA-256, source hashes, replay status and any failures. Do **not** publish restricted human or licensed raw measurements.
6. On another checkout of the **same code revision**, copy only the synthetic bundle and replay it. Run within an appropriately isolated environment because the source code is still executable research software.

## Interpretation

- `REPRODUCED_EXACT`: locally recomputed report matches all fields and the result hash exactly, with matching implementation-source SHA-256 values.
- `REPRODUCED_WITHIN_NUMERICAL_TOLERANCE`: source files and categorical results match, with differences only among finite floating point outputs within the **fixed** 1e-10 relative and 1e-12 absolute tolerances. Such a result is not bit-identical.
- `BLOCKED_SOURCE_REVISION_MISMATCH`: the installed computational source differs from the source recorded with the bundle. Recompute only with the pinned original revision; do not silently relax the condition.
- `FAILED_REPRODUCTION_MISMATCH`: a categorical, structural, count, or numerical mismatch exceeds policy. Preserve both artifacts as a failure case; do not conceal a regression.
- Malformed or tampered bundles fail integrity verification before re-execution. Neither replay nor checksum hashes prove authorship or external authenticity; only source integrity and computational reproducibility are assessed.

The replay command reads only local files, executes only the original allowlisted synthetic task, returns aggregate diagnostics and **never writes into an existing bundle**. It does not check RO-Crate conformance beyond the existing local metadata contract. Attestations, permissions and physical-model fidelity require independent processes.

## Negative control

For a disposable copy of your bundle, deliberately alter a numeric field in `result.json`, then update its `result_sha256` and `checksums.json` file digest. The old `verify` may consider such a self-consistent forged bundle valid, since SHA-256 hashes are not signatures. The new replay must report `FAILED_REPRODUCTION_MISMATCH`, demonstrating why *re-execution* is distinct from *artifact integrity*.

## External feedback request

Ask independent contributors to file an issue or PR documenting setup failures, platform differences, incomplete metadata, confusing naming and real numerical mismatches. A passing CI job is not a substitute for outside usability evaluation. Keep the validated evidence tier at S0.
