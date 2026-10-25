# V0.8: Preregistered nonhuman headform waveform screen

**Scientific maturity: S0.** This is a local, descriptive S0 research protocol. It does **not** certify a helmet, establish impact safety or concussion prevention, validate clinical EEG, or qualify the synthetic physical model.

## Why a waveform screen?

V0.7 checked input integrity and peak/RMS summaries, but a peak is not a waveform. V0.8 adds full-window descriptive resultant comparisons, peak timing, numerical integrals, shape difference and preregistered alerts. A mixed linear/rotational outcome is not collapsed into a score. All tests and included traces are synthetic.

## Preregister the analysis *before* collecting/inspecting a new trial

Freeze `examples/paired-waveform-plan-SYNTHETIC.json` or create a new local plan with:

- An analysis identifier and a fixed `[start,end]` window in seconds.
- Required **identical physical-clock timestamps** for both acquisitions. No automatic time shifting or smoothing fitted to minimize error. Independently characterize clock error and filtering.
- For each linear acceleration, angular acceleration and angular velocity resultant, thresholds for peak and time-weighted RMS percentage increases. They are **screen alerts**, not protective acceptance criteria.
- Compare a designated reference/candidate pair from the same rig, coordinate frame, impact location and protocol, with matched filters, speed and synchronization provenance.

A plan's SHA-256 is included in each output, but a hash **cannot prove** when it was created or whether it was registered before measurements were collected. For a genuine laboratory protocol, archive the plan with an independent timestamp/versioned signed protocol before testing and verify its hash against the report.

## Commands

```bash
python -m neuroshield compare-bench-waveforms \
  examples/paired-waveform-plan-SYNTHETIC.json \
  examples/bench-reference-SYNTHETIC-profile.json \
  examples/bench-reference-SYNTHETIC-manifest.json \
  examples/bench-reference-SYNTHETIC.csv \
  examples/bench-candidate-SYNTHETIC-profile.json \
  examples/bench-candidate-SYNTHETIC-manifest.json \
  examples/bench-candidate-SYNTHETIC.csv \
  --out ../paired-waveforms-SYNTHETIC.json

python -m neuroshield model-measurement-gate --out ../model-vs-measurement-blocked.json
```

Only aggregate descriptive numbers, plan and acquisition identities are written. No raw trace or local pathname is exported. The data file remains local; nothing is uploaded to the demo service.

## Mathematical definitions

For the sampled resultant \(r(t_i)=\|\boldsymbol a(t_i)\|_2\), peak = \(\max_i r(t_i)\). Time-weighted RMS uses trapezoidal quadrature of \(r(t)^2\) over the fixed window; resultant integral uses trapezoidal quadrature of \(r(t)\). The impulse-like integral is **not** a calibrated physical contact impulse or a force measurement. The shape comparison reports sample-weighted normalized RMSE relative to the reference RMS and Pearson correlation; these do not represent injury or protective performance. Comparisons use the same timestamp samples and prohibit any data-driven lag adjustment.

The uncertainty ranges use declared per-component absolute bounds multiplied by \(\sqrt{3}\) as a conservative resultant envelope. These are arithmetic bounds, **not** independently verified confidence intervals and do not account for correlated errors, sensor axes, rigid-body coupling, or protocol uncertainty.

## Gates and limitations

A comparison fails closed if any acquisition hash, origin, filter, protocol, frame, clock, speed or sample count is incompatible; if saturation/missing samples are flagged; if a declared analysis window is not covered; or if clocks have more than 5% relative jitter. A valid real nonhuman acquisition additionally needs declared local-analysis permission. That declaration is **not** legal verification or calibrated provenance.

The S0 simulator has one translational and one rotational degree of freedom and an arbitrary impact excitation. The incoming headform measurements are 3-axis rigid-body observables with independently defined acquisition frames. There is no measured input-force history, independently verified projection from 3D headform dynamics to the model's scalar head acceleration, filtering equivalence, or calibrated parameter identification. The `model-measurement-gate` therefore **always returns `BLOCKED`**. It cannot silently confer model validation from a matched waveform shape.

## Independent external data status

- [NFL engineering finite-element toolkit](https://www.nfl.com/news/finite-element-models-new-tools-for-innovation-in-football-helmet-design): FE helmets and test configurations are described, but actual model file licensing and raw measurement redistribution permissions require independent review. Do not assume an accessible landing page licenses all files.
- [Virginia Tech varsity football helmet ratings](https://www.helmet.bme.vt.edu/varsity-football-helmet-ratings.html): public methodology and summary ratings are not an unrestricted, calibration-traceable full-waveform dataset for this adapter.
- [NFL Impact Detection competition](https://www.kaggle.com/competitions/nfl-impact-detection/data): video detections and field tracking are **not** instrumented headform acceleration histories. Competition-specific licensing applies, and athlete information is not eligible for this pipeline.

No external lab waveform has been acquired, licensed, hashed, independently calibrated or compared in V0.8. To advance, obtain a written per-file license review, independent calibration certificate and bench protocol, then fix a holdout analysis plan and have a qualified laboratory review the results. No changed facemask or helmet prototype should be worn by athletes based on these software outputs.
