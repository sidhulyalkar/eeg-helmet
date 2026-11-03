# V1.11: unpaired and factorial nonhuman impact study-design preflight

**Scientific evidence ceiling: S0. No data import, statistical inference, helmet rating, clinical application or permission approval.**

## Why a second design contract?

V1.10's [matched-block preflight](study-design-preflight-v1.10.md) assumes every experimental block contains an explicitly matched reference and candidate impact. Many publicly described experiments do **not** meet this assumption. Forcing unmatched experimental conditions into pairs can create false independence and a biased estimate of treatment effects.

The [Borealis dataset](https://doi.org/10.5683/SP3/ZUZMCM) is an important *potential* external head/neck measurement source. Its public landing page describes six Hybrid III e-scooter curb crashes across helmet conditions and perpendicular/55° curb angles, with CSV and README files. The provider currently displays a dataset version number and a separately formatted citation version. The actual README contents, individual data bytes and calibration chain have **not been obtained or independently reviewed in this implementation**. Therefore no study-specific assignments or calibration values are asserted here.

Instead, V1.11 provides a general-purpose, metadata-only review of two-factor designs with one comparison variable and one stratification variable. It never converts the published six conditions into invented matched pairs.

## Synthetic demonstration

From the repository root:

    python -m neuroshield.unpaired_design examples/unpaired-design-SYNTHETIC.json --out ../unpaired-review-SYNTHETIC.json

The six fictional trials in this example only illustrate software behavior. Their factor assignments, run orders, day identifiers, angle grouping and equipment identifiers **do not describe the Borealis experiments**. All declared file identities are null because source data have not been acquired. The planned trial count is an author declaration, not independently timestamped preregistration.

The output is a reproducible SHA-256-bound **design metadata** receipt: per-stratum, per-condition declared trial and disposition counts, number of distinct rigs/headforms/days/helmets, known source limitations and explicit warnings. No identifiers, waveform values, effect sizes, significance tests or raw file paths are emitted.

## Accepted observations and blockers

- The unit is one **physical impact trial**, not accelerometer samples or video frames. A repeated impact on the same helmet or headform can be correlated with previous impacts.
- Explicitly declare comparison levels and independent impact strata. Unknown or incompatible impact angles in the same stratum cannot be silently pooled.
- Keep every planned trial record: RECORDED, METADATA_ONLY, FAILED or EXCLUDED. Failure/exclusion reasons must be declared. An unacquired source file must remain METADATA_ONLY, with no invented SHA.
- A recorded raw SHA-256 remains an **author declaration**, not proof of source authenticity, license approval or instrument calibration.
- Missing condition cells, fewer than two recorded impacts in a cell, missing speed/angle metadata, unknown order, identical apparatus clusters, reused helmets and perfect condition confounding with rig/headform/day or sequential test order are warnings.
- Contrasts are reported **within** each stratum only as coverage counts. No across-stratum pooled estimate, standard error, confidence interval, p-value or causal/protective interpretation is computed.
- An author's protocol hash is not trusted evidence that a plan was frozen before experiments began. Neither randomization nor preregistration time is independently verified.
- The tool is intentionally **not** an inference engine. A balanced cell count is insufficient to establish independent replication, assignment validity, physical transfer or generalizability.

## Scientific use after obtaining provider documentation

1. Independently confirm the actual dataset version, permitted file use, named trial identities and provider metadata through a trustworthy source.
2. Review each measurement README for acquisition clocks, units, coordinate frames, calibration, filtering, saturation and instrument limitations; keep original raw data outside Git.
3. Establish whether the actual experiment is unmatched, matched, factorial or destructive. Select the appropriate contract; do not force it to fit the software.
4. Write an exact trial-level design plan with uncertainty and all test failures. Do not invent missing run order or impact measurements.
5. Only after calibrated measurements and the analysis protocol are reviewed, consider a separately justified statistical method suitable for the true design and repeated-measures clusters.

V1.11 reads no measurement files. The existing V1.8 Dataverse inventory, V1.6 CSV probe and V1.7 measurement mapping remain distinct intake and interpretation steps. A full model-versus-measurement benchmark still requires qualified independent laboratory evidence and a context-of-use validation plan, and cannot imply football helmet safety from e-scooter data alone.

## Agentic research use

An AI research agent may inspect this metadata report and propose ways to reduce confounding or design a better follow-up experiment. It may **not** fetch restricted files, change a physical rig, authorize research, certify the design, declare a safety effect or promote S0 evidence. The separate allowlisted agent protocol retains its existing synthetic-only execution rights.
