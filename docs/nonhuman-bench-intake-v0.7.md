# Nonhuman headform intake, provenance and paired comparison (V0.7)

**Scope:** An offline research data-contract demonstration. All fixtures committed to this repository are **SYNTHETIC**. No human, athlete, patient, EEG or EMG data are accepted by this interface. These checks do **not** establish headform calibration, NOCSAE compliance, helmet safety or concussion-risk reduction. Code/data remain at evidence tier **S0**.

## Three files per locally held trial

Use an existing V0.4 `headform-manifest.json` + ten-column SI `headform.csv` accompanied by a V0.7 `intake-profile.json`. The V0.4 validator enforces shape, units, right-handed headform frame and a strict nonhuman/synthetic label. The new sidecar *binds itself cryptographically* to that bundle through `headform_bundle_sha256` and separately records the CSV SHA-256. For real nonhuman trials, keep all three files **outside the repository and outside any XERJ corpus**.

The sidecar must supply exact keys, as illustrated in `examples/bench-reference-SYNTHETIC-profile.json`:

- `source`: source URI, recorded data SHA-256, written protocol reference and laboratory-report reference
- `rights`: local-review status, license/permission references and explicit redistribution flag; this metadata is *self-reported*, not a legal opinion
- `acquisition`: anonymous trial and replicate identifiers, impact speed, sampling rate, documented filter, gravity and clock conventions, coordinate-frame and calibration references, saturation ranges
- `uncertainty`: **positive declared per-axis bounds** in SI units for each signal family, not independently verified uncertainty intervals

Never use personally identifying identifiers, athlete IDs, medical information, apparatus serial numbers that expose identities or real human recordings in these fields. The strict manifest contains no subject fields, but **cannot verify truthfulness or anonymization**. A laboratory must independently check calibration records, frame definitions, instrumentation, synchrony, authorized usage and safety.

## Run offline

```bash
python -m neuroshield inspect-bench-intake \
  examples/bench-reference-SYNTHETIC-profile.json \
  examples/bench-reference-SYNTHETIC-manifest.json \
  examples/bench-reference-SYNTHETIC.csv

python -m neuroshield compare-bench-pair \
  examples/bench-reference-SYNTHETIC-profile.json \
  examples/bench-reference-SYNTHETIC-manifest.json \
  examples/bench-reference-SYNTHETIC.csv \
  examples/bench-candidate-SYNTHETIC-profile.json \
  examples/bench-candidate-SYNTHETIC-manifest.json \
  examples/bench-candidate-SYNTHETIC.csv \
  --out ../paired-bench-SYNTHETIC.json
```

Commands never access network services or send data to the research dashboard. Outputs contain scalar summaries, blockers and hashes only, not full waveform samples. **Treat summary reports from real experiments as potentially sensitive and keep them locally until reviewed for disclosure permissions.**

## Prespecified descriptive metrics

- Peak and RMS **resultant** headform linear acceleration (m/s²)
- Peak and RMS **resultant** headform angular acceleration (rad/s²)
- Peak and RMS **resultant** headform angular velocity (rad/s)
- Candidate/reference peak difference: `100 × (candidate / reference − 1)`
- A deliberately conservative interval around each peak: `peak ± √3 × stated_per_axis_uncertainty`, clipped below at zero
- Direction labels: `lower`, `higher` or `overlap` based on whether those simple stated-uncertainty intervals separate

These *declared* bounds are not confidence intervals and have no statistical coverage guarantee; correlation, systematic bias, sampling uncertainty and impact-to-impact variability are not estimated. Never interpret a single `lower` label as an injury-risk or protective-performance conclusion. The example fixture intentionally reduces **linear** peak while increasing **angular** peak so a one-dimensional scoring algorithm cannot disguise the tradeoff.

The pair comparator **fails closed** on unequal sample counts, timestamps (no unreviewed interpolation), instrument saturation, sample gaps, mismatched frames/impact locations/protocols/filters/gravity/clock labels, inconsistent impact speed beyond an illustrative 0.05 m/s tolerance, and duplicate replicate IDs. This tolerance is an exploratory pairing safeguard **not** a NOCSAE or NFL acceptance value. No neck-force/neck-moment measurements or high-fidelity brain tissue strain are currently supported.

## Evidence status and external resources

Even when metadata states that a file is measured and rights are documented, the strongest automatic status is `REVIEW_REQUIRED`: a third-party laboratory must verify the source, measurement chain, permission scope, fidelity, and repeatability. Synthetic samples are always `BLOCKED`. No CLI path can promote S0 to S1 or mark a helmet design safe. Neither a source title nor XERJ retrieval results can qualify experimental data.

Before collecting test files, create a laboratory intake plan: impact velocities/locations, apparatus calibration and uncertainty budgets, blinding, randomized reference/candidate order, suitable replication, reference instrument comparison, data processing preregistration, and measurable headform-neck loading (if instrumented). Do not modify a certified helmet for player use under this research contract.

External primary references for planning, **not copied into this repository**:

- NFL finite-element toolkit descriptions and availability conditions: https://www.nfl.com/news/finite-element-models-new-tools-for-innovation-in-football-helmet-design (available subject to licensing; obtain the *actual file-level terms* before use)
- NOCSAE football standards index: https://nocsae.org/football-standards/ (ND081 describes a pneumatic-ram method; ND002 and ND087 are distinct equipment-performance standards; always confirm current revisions)

**Issue #11 remains blocked** until an independently licensed, instrumented *nonhuman* physical dataset, true calibration records and laboratory QC are available. Passing these software checks is not such a dataset.
