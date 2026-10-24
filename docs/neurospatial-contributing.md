# Contributing to NeuroSpatial

NeuroSpatial is a non-clinical open research track within NeuroShield. Small, auditable PRs are preferred.

## Contribution checklist

- State the scientific question, falsifiable hypothesis, and whether the claim is S0 synthetic or supported by independently reproduced human data.
- Include a fully specified sensor referencing and measurement noise model; never pass raw-montage voltages through a mismatched referenced lead field.
- Supply positive/negative controls, fixed random seeds, and tests for shape errors, nonfinite matrices and numerical instability.
- Distinguish sensor prediction loss, source localization error, resolution/point-spread, calibrated posterior uncertainty, and task utility.
- Include source permissions/licensing for forward models, anatomy and external recordings. No raw human data in Git.
- When comparing decoder quality, separate EEG-only from eye/muscle/motion-only baselines and use held-out **people/days** as appropriate.
- Keep the original NeuroShield helmet simulator unaffected by EEG inversion experiments.
- For new hardware, submit a design/safety review document before any recommendation for human use.

## Good first issues

1. Build a noise-whitened forward-model sensitivity experiment under conductivity and electrode-registration errors.
2. Implement a source-grid ablation benchmark with appropriate null/shuffled-controls and multiple noise levels.
3. Add synthetic time-series dynamics and evaluate observability versus model mismatch.
4. Design an offline BIDS validator that reports metadata only, with no raw-signal copying or uploads.
5. Write parameterized nonfunctional electrode-cap CAD fit coupons and a reviewable safety checklist.

When reporting improvements, publish failures and uncertainty, not just a visually sharper cortical heatmap.
