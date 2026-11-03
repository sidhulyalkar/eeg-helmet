# V1.10: nonhuman study-design and pseudoreplication preflight

**Scientific status: S0.** This tool reviews author-declared, metadata-only headform impact study designs. It does not read measurements, fit effects, compute p-values, establish calibration, authenticate preregistration or certify helmets.

## Why this matters

A trial containing 100,000 accelerometer samples is still *one impact*, not 100,000 independent observations. Repeated impacts on the same headform, rig, helmet unit or testing day may share noise, mechanical wear, order/carryover effects and instrument calibration errors. Therefore the **experimental unit**, grouping and impact conditions must be declared before effect estimation.

The [Bailly et al. Borealis dataset](https://doi.org/10.5683/SP3/ZUZMCM) documents six Hybrid III e-scooter falls across differing curb angles and helmet conditions. The [associated publication](https://doi.org/10.1080/15389588.2025.2462685) reports aggregate head and neck outcomes, **not** enough per-impact information in the abstract to reconstruct valid paired trials, variances or statistical significance independently. This tool cannot turn those six crashes into six matched football-facemask replicates.

## Synthetic example

Run from the repository root:

```bash
python -m neuroshield.study_design examples/study-design-SYNTHETIC.json --out ../study-design-review-SYNTHETIC.json
```

The fixture is entirely fictional. Its SHA-256-formatted strings are **placeholders**, not checked raw acquisitions or authenticated preregistration. It declares four matched blocks, alternating the order of reference/candidate impacts across two synthetic days and two synthetic headforms.

The summary reports counts and warnings only. It never exports raw measurements or trial-level sample values. The output always remains `DESCRIPTIVE_DESIGN_REVIEW_REQUIRED` at S0.

## Scientific contract

- Each `matched_impact_block` must contain **exactly one reference and one candidate** impact with distinct order, trial ID, acquisition ID and raw-data SHA declaration.
- Primary and secondary metrics must be prespecified and named with units: peak linear acceleration (m/s²), angular acceleration (rad/s²), angular velocity (rad/s), upper-neck force (N) and upper-neck moment (N·m). These are metadata labels only, not measured channel mappings.
- Both arms must satisfy the study's speed tolerance (no more than 0.5 m/s), with the within-block speed difference within that limit.
- A stratum must share its impact location, angle and target speed, with declared temperature differences no greater than 2 °C between blocks. Distinct strata are reported **separately**.
- Repeated helmet units, single-rig/headform/day experiments, fixed test order, and fewer than three matched blocks are reported as design limitations, **not** suppressed.
- Counterbalancing alone does not demonstrate randomized assignment. A plan digest supplied by the author does not prove when preregistration occurred.

The receipt reports `random_assignment_verified=false`, `preregistration_timing_verified=false`, `source_identity_verified=false`, and `independent_physical_validation=false`. No empirical effects, standard errors, p-values, injury-risk estimates or design approvals are computed.

## Important exclusions

The first implementation supports **paired, sequential** nonhuman impacts only. An unmatched, factorial or destructive crash sequence must not be force-fit into matched blocks. Declare a different research design with a separate independently reviewed protocol.

Before making causal or protective-performance claims, independent researchers must establish equipment/laboratory calibration, censoring and quality policies, assignment logs, wear/carryover limitations, frame and time alignment, cluster-aware inference, effect uncertainty, holdout or validation separation, and domain applicability. Repeat observations on a shared helmet/headform do not automatically have the same effective sample size as distinct units.

Use V1.6 `csv_probe` for local structural CSV review, V1.7 `measurement_mapping` for unverified frame/unit declarations, and V1.8 `dataverse_inventory` for metadata/byte consistency. This study-design report is a companion **design review**, not a replacement for any of those scientific gates.

## Open research and agent use

The function can help a scientist or AI agent identify study flaws *before* spending laboratory resources. Agents have no authority to fetch private data, change a helmet, approve human experiments, or promote S0 to external physical validation. See `docs/SCIENTIFIC_ARCHITECTURE.md` and Issue #11 for the empirical evidence program.
