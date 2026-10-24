# NeuroShield research evidence contract

## Levels (must never be collapsed)

- **S0 SYNTHETIC**: Demonstration traces and reduced-order equations run deterministically.
- **S1 VERIFIED NUMERICS**: Independent analytic/step-size checks and conservation audit pass.
- **S2 BENCH REPRODUCED**: Standardized, instrumented headform/neck trials compared with reference hardware and uncertainty reported.
- **S3 HUMAN SIGNAL FEASIBILITY**: Ethics-approved noncontact EEG/EMG feasibility, validated sensor coupling and data collection protocol.
- **S4 CLINICALLY VALIDATED**: Prospective external validation against clinical assessments, with regulatory engagement.

This repository remains **S0**, even if a V0.2 numerical step-size report passes. Its Pareto frontier is only a multiobjective search of a toy model, not a claim of superior protection. Passing unit tests does not upgrade it. There is no clinical injury model, human data or real protective product.

## Measurement/evidence ladder

- **Head acceleration**: simulated lumped rigid-body response, NOT measured mouthguard acceleration.
- **Cervical load**: spring-damper torsion proxy, NOT neck injury load or N_ij.
- **Brain illustration**: unitless impact response visualization, NOT strain, tissue injury, prediction or clinical risk.
- **EEG / sEMG**: synthetic artifact-bearing test signals, NOT recordings.
- **Comparison**: mechanical response relative to a synthetic reference, NOT a certified commercial helmet or established safety improvement.

## Next validation sequence

1. Establish physics baselines and numerical convergence with analytic spring/mass systems, an energy budget and an independent solver.
2. Import published NFL finite-element reference configurations and document the licensing/conditions. Build a translation manifest from test configurations to reduced-order experiments.
3. Acquire an approved headform with calibrated head-coupled kinematics, realistic neck instrumentation and controlled mechanical impact tests.
4. Perform factorial and worst-case design studies across impact locations, speeds, temperatures, repeated strikes, helmet sizes, facemask/chinstrap retention and hard-stop loading.
5. Report all regressions and intervals. Never optimize a single peak while hiding neck loads or failure conditions.
6. Only after the mechanical work: ethics-approved sensor feasibility with proper consent and clinician-led evaluation.

## Athlete privacy

- Demo API operates strictly on synthetic data; no endpoint accepts or publishes human recordings.
- Local CSV validator checks numerical shape and units only. It does NOT anonymize files or authorize sharing.
- Consent function is a policy primitive, NOT production authentication, PHI storage, encryption, anonymization, revocation propagation, or audit infrastructure.
- Before any subject data: approved consent and IRB/legal oversight where applicable, athlete-controlled scopes, vetted authentication, encryption at rest/in transit, logging, retention/deletion workflows, external security assessment, and strict separation between medical clinicians and football operations.
- No return-to-play recommendations, automated diagnoses, scoring of employees or athlete-specific predictive injury probabilities.

## Data contract

`schema_version = 0.1.0`. Time base in milliseconds from impact start. Linear head acceleration in g, angular acceleration rad/s^2, angular speed rad/s, relative torso angle deg, facemask-mount travel mm. Synthetic electrical signals in microvolts. No attempt has been made to establish accurate transfer functions or appropriate amplitudes.

CSV validator expects: `time_s,head_ax_m_s2,head_ay_m_s2,head_az_m_s2,head_gx_rad_s,head_gy_rad_s,head_gz_rad_s`.

## Future neurOS interface

One versioned `NeuralEvent` adapter should convert validated, *consented* neural timeseries and preprocessing provenance to separate analysis jobs. neurOS can handle session lineage, frozen evaluation splits, signal quality metrics and calibration while the helmet workbench owns impact kinematics and CAD design. Do not feed simulated brain response proxies as biological ground-truth labels.

## V0.2 numerical qualification (partial S1 prerequisites only)

`python -m neuroshield qualify --scenario oblique --out report.json`
checks four step sizes (1, 0.5, 0.25, 0.125 ms). The pass criterion checks relative changes of rounded peak metrics between the finest two steps under a fixed 5% tolerance. It is not a mathematical proof of convergence; it does not establish experimental validity or upgraded evidence level. Traces are deterministic but no independent solver, conservation identity, stiff-stop convergence bound or experimental uncertainty study is implemented.

## V0.2 synthetic session contract

`python -m neuroshield synthetic-session --out SYNTHETIC-session.json` and `python -m neuroshield validate-session SYNTHETIC-session.json` demonstrate a machine-readable artifact containing only supported, named synthetic channels with explicit SI or microvolt units, a common claimed timestamp convention, quality flags and a canonical hash. Timestamp monotonicity and possible gaps are validated, but no hardware clocks are actually synchronized. These artifacts must not contain names, subject IDs, or real raw recordings. No API endpoint for real data ingestion has been added.

## V0.3 numerical cross-integrator and mechanical energy audit (partial S1 evidence)

`python -m neuroshield qualify-independent --scenario all --out numerical-audit.json`

Runs 16 combinations (4 synthetic impacts x reference/suggested/stiff-low-damping/soft-high-damping designs). A separate, independently expressed RK4 solver evaluates the same three-body toy equations with the explicitly modeled spring/stop elastic potential, damping losses, external force/torque work, head kinematic peaks, and stop engagement. It compares against the original semi-implicit Euler solver, and independently checks RK4 refinement across 0.25 and 0.125 ms. The worst-per-metric numerical discrepancies, cases that fail the thresholds, source hashes, and reference energy residuals are recorded. The command exits nonzero on any failed case; CI exercises the entire 16-case matrix on multiple operating systems.

The energy relationship being checked is:

`E_final - E_initial = W_external - D_damping + numerical_residual`.

Spring potential uses `0.5*k*dx**2`; stop potential uses `3*k*max(abs(dx)-travel,0)**2` for the progressive force in this toy model, including the rotational analogue. The anchored neck's linear/torsional spring and damping elements are included. The impact waveform is a **prescribed external force**, not a realistic collision contact law.

**Numerical acceptance limits only:** cross-solver peak discrepancy <= 5%, RK4 step-refinement peak difference <= 1%, absolute energy residual / max(work, dissipation, stored energy) <= 0.5%, and exact agreement on whether the mount stop ever engages. These tolerances are engineering smoke-test conventions for this unvalidated model, not safety thresholds, model calibration, brain strain or injury probabilities. Cross-solver comparison still uses the primary solver's rounded metrics and should eventually be replaced by unrounded time-aligned traces.

Passing this audit **does not establish S1**; analytical verification of this full coupled system, mesh/contact interpretation, realistic parameter identification, and independent reproduction of the model remain outstanding. **The repository's overall evidence remains S0.** The independently written method checks numerical consistency but shares the same potentially wrong physical assumptions. Bench measurement and clinical validation are entirely absent.

An example compact artifact is checked in at `examples/numerical-audit-summary-SYNTHETIC.json`; the full report (including per-case peak values and work/energy budgets) is generated by the CLI and not committed as a claim of physical validity.
