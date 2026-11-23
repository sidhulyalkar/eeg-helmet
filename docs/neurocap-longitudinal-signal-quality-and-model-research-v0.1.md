# NeuroCap longitudinal EEG: signal quality, ergonomics and model-readiness review (v0.1)

**Dated:** 2026-11-22. **Status:** proposed design research and literature-based planning only. **Evidence ceiling:** NeuroShield S0; no custom EEG system has been built or human-tested. This complements [the first personal EEG hat feasibility plan](neurocap-personal-eeg-hat-feasibility-v0.1.md) and **supersedes any implication that the initial nominal eight-position montage should be fixed before actual cap fit and signal benchmarks**.

## Product hypothesis and falsifiability

A low-burden wearable may produce more scientifically useful longitudinal EEG than a high-density system seldom worn, **but only if valid neural contrasts survive contact drift, reference/montage changes and confounding**. Evaluate *usable neural data*, not duration recorded, number of electrodes or appearance of a clean waveform.

Proposed operating modes, not current features:
- **Discreet daily:** ordinary baseball-cap styling, soft removable insert, skin-accessible frontal and bilateral ear-centered contacts, minimal exposed hardware.
- **Research session:** optional hair-bearing central/parietal sites and separate posterior/occipital extension, plus research reference cap/headband for calibration and independently validated paradigm contrasts.
- **Sport:** **future separately qualified proposal only.** Do not use cap in place of a protective helmet, install rigid objects under one, or modify rated helmet structures/retention.

## 1. Physical architectures to compare, rather than prematurely commit

| Candidate | Rationale | Major limitations | What falsifies it |
|---|---|---|---|
| A. Cap with hair-free frontotemporal contacts | Fast setup, hidden under sweatband, simple flexible cartridge | Blink/EOG and facial EMG dominance, little posterior coverage | Raw neural contrasts indistinguishable from artifact or pressure intolerable |
| B. Bilateral around-ear cEEGrid-style contacts (commercial reference; no unlicensed design copying) | More inconspicuous, possible stable placement for natural wear | Small-amplitude differential measurements; jaw/chewing/fit and adhesive burden, narrow spatial baselines | Unable to preserve known task contrast reliably or repeated placement fails |
| C. Hybrid cap + ear + 2–4 selective hair-bearing scalp contacts | Distributes different electrode interfaces; optional broader topography | Harder cable strain relief, more variables, more setup | Does not outperform simpler A or B at matched useful wear-time |
| D. Full 8+ dry crown insert | More nominal scalp coverage | Hair/pressure, motion, individual geometry, complexity and removal | Less usable neural data per hour than simpler configurations |

**Current leading engineering hypothesis: C only if it proves better than A/B; B is the best alternate for non-cap wear.** Do not assume more channels automatically add distinguishable neural information.

Cap is a garment, **not an electrode-pressure controller**. Design a removable deformable inner frame with separately adjustable, cleanable, replaceable cartridge mounts. Hold the research amplifier in its approved housing externally for early evaluations. Use a headform-only physical model before any skin contact. Treat fit/pressure, adhesives, skin compatibility, heat, cable snag and electronics impact hazards as unresolved. Document side-to-side and front/back variation, hair density/texture variability and eyewear compatibility. Avoid unreviewed contact spring force, pointed materials or custom skin electrodes.

The first reference/ground configuration must follow the selected vendor's supported wiring/setup; do not infer it from the number of target sites. Distinguish physical sites, electrical channels and bipolar derivations. A shallow baseball cap may not reach P3/P4 or O1/O2 in reproducible positions, so **posterior alpha may require a detachable nonprotective occipital strip** or comparison with a standard full cap. Do not report standard 10-20 electrode labels without verified placement.

### Prototype placement/fit acceptance matrix
Perform repeated headform-only assembly and placement trials; declare size, forehead/hair conditions, landmarks, actual measured nominal coordinates, contact approach, insertion time, geometric deviation, assembly mass, rigid-component clearance and cable failure. Define independent fits, not just repeated photographs of one assembly.

Human comfort duration is not a first-stage engineering target without separate qualified review; develop stop criteria for skin irritation, headache, discomfort, heat, electrode motion and electrical faults before any independently reviewed human pilot.

## 2. Information-theoretic and inverse-model limits

Scalp potentials obey a forward-model abstraction:

    v(t) = R L(theta) s(t) + a(t) + epsilon(t)

where s is a high-dimensional neural source distribution, L(theta) is the uncertain lead field depending on head geometry/conductivity and montage, R captures reference/differential measurements, a is physiological/kinetic/electrode artifact and epsilon instrument noise. A sparse EEG montage cannot uniquely invert L, even with unlimited repeated samples, because different sources may share the same scalp projection or lie in a null space. **Do not describe a learned spatially sharper map as physically resolved without independent reference truth.**

EEG contains some contributions from deep sources but is generally biased toward large synchronous cortical populations; avoid the absolute claim that it measures *only* superficial cortex. The reference is a physical part of a potential-difference observation; rereferencing cannot reconstruct an unmeasured absolute potential.

To maximize *distinguishable information*, optimize placements against a **specific observable** and compare reduced configurations through ablations. In an independently specified head/forward model, possible exploratory placement criteria include the smallest nonzero singular values of the observation operator over a predeclared subspace, condition number and D-optimal design; these are **not physical validation** and can be brittle to conductivity, electrode misregistration and reference.

## 3. Quality-first acquisition and acceptance

**Proposed metadata per raw sample/block:** session ID, immutable channel names, electrical differential/reference path, sampled counter, source clock, host timestamp, calibrated session clock with uncertainty, unit, gain, ADC range, firmware/hardware ID, physical electrode map with *measured/nominal* flag, signal-quality annotations and privacy class.

Separate:
- raw measured samples (unaltered, lossless);
- acquisition/coupling flags (packet loss, saturation, flatline, baseline drifts, unusual noise floor, common-mode/line noise, contact quality if supported);
- physiological artifact tags (blink, saccade, jaw contraction, temporal EMG, ECG contamination);
- motion/contact tags (hat slip, motion sensor, sweat/hair interface effects);
- analyses and confidence (derived features; preprocessing version; rejected/abstained intervals).

An electrically plausible waveform is **not** proof of neural origin. Require known stimulus-locked/physiology contrasts where plausible, commercial reference comparisons and reproducibility on separate independent fittings and days. For low-channel recordings, do not assume ICA or ASR can perfectly separate artifacts; always preserve the raw stream and uncertainty.

**Usable neural minutes** should be reported by task and motion regime, rather than treating all data as equal. Candidate metrics: `total_minutes`, `acquired_minutes`, `quality_accepted_minutes`, `task_contrast_reproducible_minutes`, `mean_setup_minutes`, `comfort_dropouts`, `signal_yield_by_electrode`, `coverage_of_recording_context`. Signal thresholds depend on the measured task and reference and must be prespecified. Mark *unmeasured* separately from *failed* and *zero*.

## 4. Data/model architecture aimed at future pretrained networks

Design device-neutral typed **multimodal synchronized sensor manifests** with optional EEG, EOG, EMG, ECG, PPG, IMU, manually tagged tasks, optical/acoustic event *features*, and battery/contact telemetry. Do not assume their missingness is random. Clock maps carry uncertainty and can fail closed if alignment is unverified.

Quality-aware feature formation:

    input = (raw EEG tokens, channel coordinates, reference graph,
             contact/missing masks, motion features, contextual labels,
             clock uncertainty, device/session metadata)

A research hypothesis is to compare a simple feature model with channel-aware pretrained encoders, not to assume a large model solves inversion or inference. Each result must state whether it exploits artifacts, recording session, montage, time of day, speaker/audio context or individual identity.

Suggested benchmark ladder:
1. **Only context**: clock time, keyboard/app labels, experiment state.
2. **Only IMU/EMG/EOG**: a strong movement/ocular artifact negative control.
3. **Only EEG**, carefully quality-gated, simple spectral/ERP and regularized models.
4. **EEG + permitted physiological sensors**.
5. **EEG foundation-model embeddings + limited participant calibration**.
6. **Multimodal fusion** with reliability-aware fallback or abstention.

Evaluate held-out **entire days, fresh re-fits and electrode perturbations**; use chronological holdouts and report distribution shift, per-class calibrated errors and false positives. Do not random-split adjacent windows across train/test. For interventions or claims about effects of activities, use predeclared within-person crossover/counterbalanced designs with relevant negative controls rather than just observational correlations.

Possible future models to benchmark: LaBraM, EEGPT, CBraMod, BrainBERT (intracranial context; not a scalp substitute), and channel-flexible EEG-Arena/NeuroInfra references. Pin exact weights, licenses, training dataset provenance and code; avoid importing protected human data into the NeuroShield S0 repo. Interpret claims against mixed findings across EEG-Arena and NeuroAtlas. ECoG and intracortical speech decoding performance is **not portable evidence** of speech decoding from a baseball cap.

## 5. User experience to prototype deliberately

The user should see:
- **Fit:** 'two contacts need adjustment', not an invented wellbeing percentage.
- **Now:** 'quality-gated recording is available', with confidence/coverage.
- **Day:** activity events layered on quality-accepted physiological features and missingness.
- **Weeks:** repeatability and comparisons over equivalent activities, sleep/rest, recording setup and times.
- **Studies:** exact controls, held-out sessions, null outcomes, uncertainties and reproducibility receipts.

Aesthetic principle: cap remains recognizably an ordinary cap; no large exposed ring, no dangling wire bundle, no sharp rigid electronics against head, no light-emitting status indicator in line of sight. The outer cap and skin-contact inserts are independently washable/replaceable subject to eventual material review. The system must remain useful **even when the hat is not worn** through manual logs and separate wearables, without pretending that contextual data are EEG.

For microphones, default to no raw recording and no external upload. Optional on-device VAD/speech-turn/ambient-event extraction requires explicit user control and visible state; remove or aggregate audio immediately unless the user specifically enables a governed experiment and bystanders are accounted for. Neurodata should not be automatically fed to an LLM, a hosted CAD service or XERJ.

## 6. Go/no-go experiments (order matters)

**A. Inverse and placement simulation (S0):** synthetic lead fields, reference changes, contact dropout and electrode misregistration. Compare 4 frontal vs 4 frontal + 2 ear vs hybrid vs conventional cap against task-specific distinguishability in a *declared* synthetic model. Include counterexamples with unidentifiable source configurations.

**B. Headform-only physical prototype (S0):** modular mount CAD, exact fit measurement, cable movement tests, removal and cleaning study; do not assert human wear safety.

**C. Commercial acquisition reference:** qualified electrical/skin setup, controlled calibration procedure, commercial cap/headband on separate supported protocol and commercial ear-based sensor if feasible. Human data remain outside Git, retrieval indexes and agent interfaces.

**D. Stable physiology:** eyes-open/eyes-closed with posterior signal if truly present; blink/EOG, auditory paradigm, jaw artifact controls; determine which configurations actually yield known independent EEG contrasts.

**E. Motion:** stationary vs voluntary nodding, talking, walking in a controlled space; force classifier to discriminate EEG contribution from IMU-only and EOG/EMG artifacts. Report rejection rates and clean data coverage.

**F. Longitudinal drift:** repeat new fit across distinct mornings/afternoons and days, examine accuracy under day holdout, recalibration cost, tolerable setup burden and skin comfort.

**G. Adaptive modeling:** only after D–F pass, train subject-specific calibration and compare the foundation-model backbone to classical baselines with true held-out days.

**H. Sports:** separate protective-equipment and electrical/thermal/collision qualification proposal. No authorization to place prototypes beneath protective helmets.

## 7. Research sources reviewed 2026-11-22

- EEG-Arena (Sept 2026 preprint): https://arxiv.org/abs/2609.32743
- NeuroAtlas (May 2026 preprint): https://arxiv.org/abs/2605.14698
- Multi-dimensional EEG FM generalization evaluation (CHIL 2026): https://proceedings.mlr.press/v333/kommineni26a.html
- EEG montage robustness (Sept 2026 preprint): https://arxiv.org/abs/2609.36288
- Wearable multi-sensor EEG review (July 2026): https://pmc.ncbi.nlm.nih.gov/articles/PMC13406779/
- Ear-EEG focus comparative study (2023): https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2023.895094/full
- cEEGrid flexible around-ear EEG (2017): https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2017.00163/full
- BrainBERT intracranial representation learning (2023): https://arxiv.org/abs/2302.14367
- CORTEG scalp-to-ECoG model transfer (May 2026 preprint): https://arxiv.org/abs/2605.10337
- ECoG speech prosthesis (2025; not feasible with scalp cap): https://www.nature.com/articles/s41593-025-01905-6

Sources motivate hypotheses; they do not prove this specific prototype design, manufacturer safety, regulated use, clinical validity, raw-data access permissions or user-specific outcomes. Full expert review, independent empirical reproduction and governance remain outside scope.
