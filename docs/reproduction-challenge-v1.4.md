# Independent reproduction challenge (V1.4)

**What this is:** a bounded, offline computational exercise for a researcher who did **not** write NeuroShield. It is **not** itself an independent reproduction, an authenticity check, calibration proof, or helmet performance study. All experiments remain S0 synthetic.

## Run as an independent participant

1. Choose a clean Python 3.10+ environment, preferably on a second OS or machine. Record the exact source commit and package version in your own lab notes.
2. Clone the repository (or install a reviewed release wheel) and install the package. No dataset downloads, GPU, LLM, XERJ or private account are required.
3. From a directory *outside the repo* run:

   ```sh
   python -m neuroshield.reproduction_challenge run ../neuroshield-repro-01
   python -m neuroshield.reproduction_challenge verify ../neuroshield-repro-01
   ```

4. Record the two task/result hash receipts, source revision, OS/Python, execution time and any setup failures in `examples/reproduction-feedback-template.md` (do not put your identity, private paths or unrelated data in a public issue).
5. Use the standard `neuroshield.reproduction` command on each of the two bundles if you want the individual replay details.
6. Submit a report or PR **as an outside researcher**. Only an actual external reviewer may establish independent reproduction. An automated CI run cannot satisfy Issue #19 on its own.

## Scientific and technical policy

The fixed challenge runs **one oblique synthetic impact** using default parameters and **the 16-case synthetic numerical audit**. Both are predetermined by versioned code, not selected based on favorable results. No user-defined operations, output commands, URLs, human/neural recordings or physical equipment access are admitted.

Output is a new directory with `impact/` and `numerics/` standard four-file research bundles plus `challenge-report.json`. Case failures are retained in the report and later cases are still attempted. Failure codes are sanitized to avoid copying local file paths or arbitrary exception messages into public artifacts. Keep actual restricted dataset files entirely outside this workflow.

`run` returns an exit code of 0 only if both computations replay locally. `verify` replays both **against the installed implementation**, checks that the exact frozen task was run, and rejects missing or modified bundles. Either command returns exit code 2 for nonreproduction. Verification is read-only. Each bundle retains V1.3 hash-bound RO-Crate metadata. The composite challenge report is not digitally signed; self-declared operating system values and hashes do **not** authenticate the person or the machine.

### What a passing result means

* **PASS_COMPUTATIONAL_ONLY**: the fixed synthetic tasks were reproduced in the given environment. Does not imply external scientific independence.
* **FAILURES_RETAINED / NOT_REPRODUCED**: a task failed, an artifact was missing or modified, or replay disagreed. Publish failures rather than hiding them or retrying silently.
* **S0**: no source-generated safety score, physical calibration, injury prediction, athlete data or clinical conclusion. The 3-body mechanical model is illustrative.

## Acceptance criteria for Issue #19

An independent scientist reproduces the pinned challenge on a clean environment; their report includes source commit, exact wheel/package version, platform, both task/result identities, failed attempts and qualitative setup feedback. A maintainer can independently replay the supplied public bundles with identical sources. Feedback improves the code, but **no one automatically upgrades evidence level**.
