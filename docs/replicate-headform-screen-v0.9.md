# V0.9: replicate-level nonhuman headform screening

Run an **offline, local-only** study of separately recorded matched reference/candidate impacts. The independent unit is an **impact trial**, not a time sample. The report includes trial-level peak changes, mean/median/min/max/sample standard deviation, sign disagreement across trials, and a preregistered worst-case regression screen. This is **descriptive only**: no safety acceptance, statistical significance, calibration or concussion prevention claims.

## Start with fully synthetic data

```bash
python3 -m pip install -e .
python3 scripts/make_replicate_demo.py ../neuroshield-replicate-demo
python3 -m neuroshield.replicate_study ../neuroshield-replicate-demo/study-SYNTHETIC.json --out ../neuroshield-replicate-demo/report.json
python3 -m unittest discover -s tests -v
```

The generator refuses to overwrite existing destination directories. All generated data is clearly marked synthetic; synthetic repeats do not establish empirical reproducibility.

## Real-data eligibility

The study JSON pins schema, origin, apparatus, impact location, protocol, speed and tolerance, three preregistered peak-regression thresholds, and all pair paths. Each arm references a V0.7 **profile/manifest/CSV** triple. Local paths must be within the study directory; traversal, symlinks, mismatched protocols, duplicate raw acquisitions and duplicate replicate IDs are refused. Existing headform intake gates reject missing samples, saturation and missing analysis-rights review. An S0 status is preserved even if real data becomes eligible for analysis.

The code reports only aggregate measures and pseudonymous data fingerprints, not raw waveforms, local file paths or human signals. Do not commit restricted third-party datasets, calibration certificates with personal information, or human recordings. No optimization of clocks or alignment is performed by this module.

The `NO_PREDECLARED_REGRESSIONS_FLAGGED` screen is **not** proof of equivalence or reduced concussion risk. Severe impacts, impact vectors, neck forces, reproducibility across independent apparatus and measurement uncertainty require separately approved methods. No multiple-comparison or confidence-interval inference is performed.

## Relevant external candidate sources, not imported

- Sciacca et al., *In-Lab Helmet-Mounted IMUs and Headform Impact Kinematics Dataset for Ice Hockey*, Zenodo 22092814 (2026): dataset metadata public, **files restricted**, access and permission verification required; hockey apparatus and signals not automatically comparable to football fixtures.
- Decker et al., *Development and Multi-Scale Validation of a Finite Element Football Helmet Model*, DOI 10.1007/s10439-019-02345-7: includes published validation methods and additional figures. Reconstructing time series from plotted figures is **not** equivalent to obtaining original calibrated waveform files.
- NFL/Biocore helmet FE toolkit: model redistribution and derivative use remain subject to its license and citation policy.

Issue #11 remains open until independent, licensed, calibrated nonhuman recordings can actually be evaluated.
