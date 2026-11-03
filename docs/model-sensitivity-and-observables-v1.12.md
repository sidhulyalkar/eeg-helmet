# V1.12: model-form sensitivity before attempting calibration

**Evidence remains S0.** This is a deterministic, synthetic, offline audit of the current illustrative facemask/shell/head equations. It does not estimate physical properties, identify real helmet parameters, review human data, authorize protected datasets or assess injury risk.

## Why this scientific experiment matters

The reduced-order system contains five freely adjustable parameters:

- Facemask mount stiffness, damping and available travel
- Shell-to-head liner stiffness and damping

Numerical integration reproducibility is necessary but does not establish whether these five parameters can be learned independently from available observations. Some parameters can affect the same output in nearly the same way, and some may have little effect on peak metrics under certain impact configurations.

The [guidelines for mechanistic modeling](https://pmc.ncbi.nlm.nih.gov/articles/PMC11442102/) distinguish structural from practical identifiability. Local sensitivity analysis is a useful early diagnostic, but a parameter-pattern cosine or finite-difference Jacobian is **not** a formal identifiability proof or a calibrated posterior distribution. [ASME V&V 40](https://www.asme.org/codes-standards/find-codes-standards/assessing-credibility-of-computational-modeling-through-verification-and-validation-application-to-medical-devices?productKey=C08418) further emphasizes the context of use when assessing model credibility. This project does not claim compliance.

## Reproduce the synthetic calculation

From the repository root, with no external data:

    python -m neuroshield.model_diagnostics --scenario all --preset default --out ../sensitivity-default.json
    python -m neuroshield.model_diagnostics --scenario all --preset suggested --out ../sensitivity-suggested.json

The tool reads only the allowlisted four simulated scenarios and two built-in parameter presets. It never optimizes parameters, reads a dataset or modifies original scientific parameters.

For each of the five peak metrics and each parameter, it evaluates **central finite differences** at 1% and 0.5% relative perturbations. The normalized elasticity is

    E_ij = ( y_i(p_j*(1+h)) - y_i(p_j*(1-h)) ) / (2*h*y_i(p))

when the baseline metric is materially nonzero. The tool preserves an unnormalized derivative when this denominator cannot support a relative measure. It compares the two steps and flags local derivative instability, including effects of travel-stop switching and peak-time changes.

A pairwise **cosine similarity** across parameter-sensitivity columns can flag nearly identical effects on the chosen output set. Thresholds (0.98 pattern similarity, 0.01 weak RMS elasticity, 0.25 derivative-step difference) are **heuristics**, not hypothesis tests, confidence bounds or physical significance thresholds.

## Absolute model-versus-measurement limits

| Toy peak output | What it is | Why direct measured comparison is blocked |
| --- | --- | --- |
| Peak head acceleration in g | One-axis lumped head acceleration | A 3D accelerometer's resultant is not the same observable |
| Peak angular acceleration | One-axis rotational acceleration | Does not specify 3D head axes, sensor location or inverse transform |
| Peak angular speed | One-axis rotation speed | Does not represent the magnitude of a 3D angular-velocity vector |
| Peak neck torque proxy | Fixed torso spring/damper anchor reaction | **Not** a calibrated six-axis upper-neck load-cell moment |
| Peak facemask mount deflection | Relative scalar displacement | Not a measured geometry, displacement transducer or safe design travel |

Even a perfectly stable Jacobian does not make these outputs directly comparable with Borealis head/neck instrument channels. Such a comparison requires a physically justified **forward measurement operator**, identified units/frames and sensor location, apparatus matching, uncertainty, and independent review.

## How to interpret a report responsibly

1. Record the source-bound simulation fingerprints and selected scenario/preset in the report.
2. Review peak derivative instability before interpreting any parameter comparisons: an absolute peak can switch between competing timestamps or hit the modeled travel stop.
3. Inspect weak parameter sensitivity and high absolute cosine values only as **follow-up hypotheses** about which model observables deserve further investigation.
4. Compare default and suggested presets. A local result is not global, and a parameter might become influential in a different region.
5. Select the smallest physical experiment that could *falsify* a model assumption. If the model cannot represent the observable, change the model or the measurement plan rather than calibrating a proxy.
6. Do not optimize against a public dataset and then reuse the same impacts to claim held-out validation. Preserve all failed configurations and actual trial units.

## Implications for the architecture

NeuroShield should remain a modular monolith with three different kinds of evidence:

- **Numerical verification:** independently implemented solver and energy audit.
- **Sensitivity/observability diagnostics:** this S0 module studies what the current equations can reveal, without measured data.
- **Physical validation:** still missing, requiring an independent, licensed and calibrated nonhuman experiment with comparable model outputs.

The external Borealis measurement README and file-level calibration descriptions must be inspected before any forward model comparison. The existing unpaired/factorial preflight helps avoid invented matches but does not establish measurement compatibility. The next *empirical* milestone remains one verified, reproducible nonhuman measurement and an explicit model discrepancy report, not more infrastructure.
