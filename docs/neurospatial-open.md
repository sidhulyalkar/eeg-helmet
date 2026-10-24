# NeuroSpatial Open: EEG source identifiability research

**Status: S0, synthetic mathematical baseline.** This is a new, independent research module within NeuroShield, not a helmet safety subsystem. It is neither a human EEG reconstruction product, thought reader, diagnostic device, nor behavioral treatment.

## Run the executable experiment

Install the optional NumPy dependency without changing the existing zero-runtime-dependency NeuroShield dashboard:

```sh
python -m pip install -e ".[neurospatial]"
python -m unittest discover -s tests -v
python -m neuroshield.neurospatial --out synthetic-inverse-report.json
python -m neuroshield.neurospatial --channels 16 --sources 96 --seed 2026 --out synthetic-16ch.json
```

Commands work with Python 3.10+ on supported platforms. The generated JSON has `origin=SYNTHETIC`, `evidence_level=S0`, and a SHA-256 content identity. The data generator uses a **one-dimensional Gaussian spatial mixing kernel**, not physical head tissue, geometry, cortex, or FEM/BEM. Do not interpret its numeric scores as EEG performance.

## Mathematical contract

For a fixed reference, the linear forward problem is

```text
y = L x + noise
L: (M independent referenced measurements) x (N modeled source amplitudes)
```

If N > M, L has a nontrivial nullspace. For any z with Lz = 0, x and x + z are indistinguishable from a single noiseless observation. A tiny scalp prediction residual does not establish a correct source estimate.

The implemented Gaussian zero-mean estimator computes

```text
W = Q L^T (L Q L^T + Gamma)^(-1)
posterior_mean = W y
posterior_cov = Q - W L Q
resolution = W L
```

Here Q and Gamma are **positive definite input covariances**. In the implementation a linear solve is used instead of explicitly computing an inverse. Posterior uncertainty is conditional on Q, Gamma and L, and does not cover biological/model mismatch.

Real scalp EEG is referenced. In the reference-to-one-electrode example, M physical electrodes yield M-1 independent differences. Independent equal-variance raw electrode noise induces nonzero correlations between the differences because they share a reference. The code models that covariance instead of treating referenced noise as independent.

The module also demonstrates:

- Noise-whitened singular values to inspect weakly observed modes.
- A nonzero source perturbation whose contribution to the scalp voltages is zero up to numerical precision.
- A known linear-state observability matrix stacked across time. Its increased rank is **not** evidence real neural dynamics are known or reliably identifiable.

## Falsifiable next experiments

| Gate | Dataset | Baselines/controls | Required evaluation |
|---|---|---|---|
| N1 | Analytic & simulated forward fields | Known ground truth; model mismatch; shuffled priors | Source localization, resolution, calibration and coverage |
| N2 | Public EEG with known sensory/motor events | Independent session, sham forward model, EOG/EMG controls | Held-out event prediction, sensor-space fit and uncertainty |
| N3 | Dataset with digitized electrode coordinates and anatomy | Template versus subject-specific BEM/FEM | Held-out subjects; forward-model sensitivity and co-registration errors |
| N4 | Consented repeated recordings | EEG-only, EOG/EMG-only, movement and contact-quality control | Cross-day calibration costs, abstention and artifact robustness |
| N5 | Voluntary behavioral interventions | Behavioral-only baseline, randomized no-cue/control | Predeclared outcome, adverse effects, and causal benefit |

**No dataset is a cortical source ground truth merely because a source image can be computed from it.** For real EEG, use MNE-Python and measured sensor layouts; archive estimator, coordinate system, reference, source grid, noise-covariance method, anatomical model license, excluded epochs, and complete provenance. Do not use random trial splitting if repeated trials from the same session or person can leak across train/test.

NeuroSpatial should eventually expose a **neurOS benchmark adapter**, but no adapter is implemented in this PR.

## Interpretation gates

1. S0 SYNTHETIC: numerical identities, simulated mixing, deterministic tests only.
2. S1 REAL SIGNAL FEASIBILITY: publicly licensed and/or appropriately consented EEG; known acquisition geometry and quality validation; no anatomical claim.
3. S2 INDEPENDENT REPRODUCTION: independent dataset and realistic head model, validated registration, sensitivity and calibrated uncertainty.
4. S3 PROSPECTIVE UTILITY: pre-registered subject/session-disjoint prospective research with appropriate governance.
5. Clinical, thought-to-text and behavioral-efficacy claims: **not implied by any preceding level**. They each require separate evidence.

## Source material

- MNE-Python inverse modeling: https://mne.tools/stable/auto_tutorials/inverse/10_stc_class.html
- MNE forward modeling: https://mne.tools/stable/auto_tutorials/forward/30_forward.html
- EEG-BIDS specification: https://bids-specification.readthedocs.io/en/stable/modality-specific-files/electroencephalography.html

## Boundaries

The existing helmet mechanics and dashboard remain S0 synthetic, and there is no runtime connection between helmet impact simulations and NeuroSpatial. Never treat a toy source reconstruction as brain strain, concussion risk, detected thoughts, clinical assessment, or actual user behavior.
