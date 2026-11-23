# NeuroCap: modular all-day EEG baseball-cap research feasibility (v0.1)

**Status:** design proposal only; nonclinical; no completed electronic, mechanical or human-wear validation. **Evidence ceiling:** NeuroShield S0. **Prepared:** 2026-11-22. This is a proposed *new* nonprotective headwear track, not a finished build, approval, human-research protocol, safety certification or modification of a sports helmet.

**Related documents:** [EEG headwear builder guide](eeg-headwear-build-guide.md), [research evidence contract](research-contract.md), [scientific architecture](SCIENTIFIC_ARCHITECTURE.md), [CAD and retrieval toolchain](cad-and-retrieval-toolchain.md), [open EEG ecosystem](open-eeg-ecosystem-and-community.md).

## 1. Goal and falsifiable scope

Explore a **removable segmented electrode-positioning frame under an ordinary 6-panel baseball cap**, initially using an existing research EEG system rather than custom human-connected electronics. Acquire time-aligned EEG, motion and manually labelled task events, and later separately supplied ECG/PPG and acoustic *features*. Determine whether sufficient signal quality and comfort exist for useful repeatable within-person analyses across sessions.

Primary questions:
1. Can a flexible frame indexed to cap sweatband/headform landmarks maintain nominal electrode positions and tolerable fit without assuming universal scalp geometry?
2. How does dry-electrode quality change during head motion, speech, jaw contraction and outdoor-like movement, compared with a vendor-supported reference headband?
3. Are task effects distinguishable from ocular, muscle, contact, environmental, motion and time-of-day covariates on **held-out days**?
4. Can hardware and behavior clocks be calibrated with recorded residual error rather than asserting sample-perfect alignment?

The **first scientific deliverable is a testable feasibility specification**, not all-day thought decoding, diagnosis, concussion detection, or sport use.

## 2. Proposed physical design (nonwearable headform prototype first)

Base garment: one ordinary fabric 6-panel baseball cap. Do not alter any certified impact protection. Treat the pictured cap type as a design *reference*, not as measured geometry.

A. **Independent insert:** a thin flexible interior horseshoe along the sweatband (front/temporal region), with 2–3 removable longitudinal ribs traversing frontal, central and parietal headform regions. Index the insert to adjustable fiducials/retention points; the garment provides concealment, not calibrated electrical contact pressure.

B. **Replaceable electrode cartridges:** separate flat-contact modules for hair-free frontal/temporal locations and commercial dry comb-contact carriers for hair-bearing sites. No DIY conductive spikes or improvised skin-penetrating components. Electrode units must be cleanable, individually replaceable and position-adjustable. Quantify electrode force/deflection on *instrumented headforms* before proposing human use; avoid invented safe-pressure claims.

C. **Cable management:** flexible isolated wiring path along ribs, strain-relieved at each cartridge, no wire loop over the brim, no sharp exposed or rigid edges, nothing that constricts the head, obstructs vision or entangles with moving equipment.

D. **Electronics:** for initial trials retain the commercial amplifier in its vendor case, **outside the cap** in a separately supported bench/pouch location; do not conceal a hard PCB or lithium pouch in an impact contact zone. Only after qualified electrical/thermal/mechanical review consider a soft detachable enclosure at the rear of a *nonprotective* cap.

E. **Additional modalities:** a documented head IMU; optional commercial ear/forehead PPG only after contact and motion testing; separate commercial chest ECG such as Polar H10 if raw ECG is required; optional device microphone with explicit user-controlled VAD / event extraction and no default raw conversation retention.

Critical fit caveat: a conventional cap may not reach posterior occipital O1/O2 sites; do **not** mark them achieved on a shallow cap. Accept fewer verifiable positions, or design a separate optional nonprotective occipital band.

### Nominal 8-channel *target* montage, not established placement

Candidate target sites: Fp1, Fp2, F3, F4, C3, C4, P3, P4. Ears/mastoids or vendor recommended reference/ground location must be separately declared and reviewed; these eight names do **not** specify a complete valid electrical setup. Consider 4-channel frontal/central subset for first mechanical prototype; compare against the vendor placement baseline. Additional EOG/EMG channels consume amplifier channels unless a separate acquisition device is used. Individualized electrode positions are unknown until measured and should not be labelled as verified international 10-20 sites.

Design parameters requiring measurement: headform circumference, sagittal/coronal contour, cap crown clearance, hair thickness, sweatband placement, electrode carrier travel, cartridge contact angle, cable minimum bend radius, assembly mass and ease of release. Use **millimeters**, explicit coordinate axes/fiducials, revision history and export provenance. Do not upload personal head scans to hosted CAD by default.

## 3. Instrument strategy and staged purchasing

- **Reference amplifier (candidate, not a stock claim):** OpenBCI Cyton 8-channel, ADS1299, nominal 250 Hz, vendor USB radio dongle, microSD logging. Research-oriented, but its stock form is too bulky to prove a comfortable hat. Follow the manufacturer's battery-only setup and safety instructions.
- **Reference contacts:** original vendor-supported EEG headband/electrodes (or appropriate vendor electrocap) and its documented cables/reference; measure baseline before fabricating the insert. Availability and compatibility must be checked at ordering.
- **Headform mock-up:** second inexpensive copy of the cap, nonconductive flexible CAD-print prototype parts, adjustable textile tabs, rigid headform, small force/deflection measurement jig, calipers and lab-scale; no attachment to an impact helmet.
- **Context and physiology:** prefer phone/desktop event markers and existing wearable data exports; choose commercial ECG if required. Low-cost PPG breakout modules are **bench/phantom components only** until a safety and skin-contact design is reviewed.
- **Do not order yet:** custom analog front-end PCB, dense dry electrode array, hard power bank for the cap, integrated microphone/PPG PCB, or any sports-helmet mounting hardware.

Prices and supply should be confirmed against current first-party stores before deciding. A preliminary off-the-shelf Cyton and dry headband reference kit can cost much more than a simple consumer EEG headband.

## 4. Acquisition and timebase design

Keep NeuroShield's dependency-light S0 core intact. New integrations are **optional adapters** behind tested, versioned contracts, not a direct extension of the synthetic demo into unrestricted human recording.

Proposed streams:
- EEG: eight nominal channels at 250 Hz when using Cyton, always record sample counter, reference, gain, units, channel-quality flags, sample loss, amplifier firmware, raw status and source.
- IMU: target 100 Hz or higher with recorded device-local timestamps, calibration/orientation and mounting location.
- ECG: separate SDK-supported commercial device if enabled; raw ECG availability and true sampling behavior checked independently (e.g. Polar H10 reports 130 Hz).
- PPG: target 25–100 Hz as a *design target only*; record optical site, signal quality, skin interface, waveform quality and firmware; derived pulse rate must not be confused with ECG.
- Microphone: default off. Optional on-device voice-activity and acoustic event *features* only, without storing raw speech or bystander audio. Dedicated consent + visible recording status + hardware/user opt-out for more sensitive modes.
- Task events: explicitly tagged button/key presses, named app sessions, voluntary self-report, experiment cues, protocol start/stop and annotator uncertainty.

Use device-monotonic samples and measured host clock transforms. For every device clock, estimate an affine map from its monotonic clock to the session clock: **t_session = a * t_device + b**, with calibration observations, drift update, uncertainty interval and uncorrected raw timestamps retained. Arrival timestamp != neural acquisition time. Cyton SD card acquisition is useful for outages, but post hoc correspondence to phone or computer events remains an independent, unsolved problem without measurable anchors. LSL/XDF can preserve clock-offset measurements during synchronized laboratory recordings, not magically cure unknown source latency.

Storage strategy:
- private encrypted raw session directory outside Git and outside any approved search index;
- lossless raw signal plus device sample counter/timestamps, sensor manifest, sync-calibration receipts, event table and QC table;
- BIDS EEG/derivatives export for permitted recordings; electrode coordinates only when observed, with documented coordinate frame; independently documented other-modality exports;
- explicit data retention, deletion and export controls; no cloud upload or agent access by default.

## 5. Processing and interpretation

Never infer an individual's exact thought, internal speech, diagnosis, emotional truth or intent from the multichannel signal alone. A useful causal model must treat EEG as a mixture:

    X_eeg(t) = L * S_neural(t) + A_eye(t) + A_muscle(t)
               + A_motion/contact(t) + N_instrument(t)

This forward model is schematic: source distribution, lead field and artifacts are uncertain and often nonidentifiable at sparse montage density. Accelerometers and PPG help identify some artifact and physiological covariates, but cannot simply remove all confounds.

Recommended staged processing:
1. Original immutable raw data with unit/scale/reference and clock audits.
2. Per-channel signal-quality metrics: flatline, saturation, line noise, missing samples, transient spikes, contact/impedance proxy when supported, movement and cable sway.
3. Named preprocessing variants (not one hidden filtered truth): re-reference, filtering, ICA/ASR only where assumptions and channel count justify them; preserve rejection masks and rejected intervals.
4. Task-baseline analyses: eyes-closed vs eyes-open alpha; blink/EOG checks; jaw movement; task onset/offset; simple event-related contrasts; assess artifacts explicitly.
5. Classifier baselines: signal-quality-only, IMU-only, contextual event-only, EEG-only and full multimodal fusion; compare macro F1/balanced accuracy and calibration including abstentions. Report class prevalence and data coverage.
6. Freeze time-blocked and entire-day/session holdouts; avoid leakage from adjacent temporal windows, repeated cues, task order, time of day and event labels derived from the same sensor being predicted.
7. Explore temporal models only after beating these simple baselines, using confidence intervals based on independent sessions (not a million correlated sliding windows).
8. Longitudinal dashboards should report **observations + uncertainty + QC coverage** and distinguish behavior labels from neural inference.

## 6. Verification plan and explicit gates

These are **proposed research targets**, not validated safe thresholds or guarantees.

**G0 Software-only:** synthetic multimodal session; schema and unit negative tests; dropout, swapped clock, missing ground/reference declaration, nonmonotonic timestamps, impossible geometry, provenance loss; zero human data.

**G1 Headform mock-up:** cap insert with labelled *nominal* contacts; report several headform sizes and garment adjustments; repeatable removal, realistic clearance, component isolation and failure surfaces. No electrical skin contact.

**G2 Commercial reference system:** only with qualified review of manufacturer safety instructions and a permitted self-study protocol, measure standard reference headset at rest and during controlled simple paradigms. Record all failures and comfort observations; do not imply medical approval.

**G3 Bench synchronization:** phantom/test-signal and independently timed events; measured end-to-end trigger delay distribution, clock drift, packet loss and recovery. Initial *engineering evaluation targets*: less than 1% unexplained sample loss in a stationary pilot and documented latency/clock residual distribution. Targets must be revised from actual measured performance.

**G4 Candidate vs reference:** controlled repeated independent fits and sessions, counterbalanced conditions, comparison of signal quality and task-contrast reproducibility; preregister electrode set and preprocessing. Candidate must **not** be reported as better based solely on filtered traces or a classifier trained and tested within one session.

**G5 Wearability:** short controlled use first; independent fit/comfort/electrical/thermal/skin safety review before increasing duration. Stop promptly if symptoms, scalp irritation, discomfort, heat, hardware movement or unexpected fault. Wear duration is gated by evidence, not an all-day marketing promise.

**G6 Unstructured day:** only after earlier gates; soft event capture, dropout/coverage reporting, privacy-by-default and individual day holdouts. Do not use a still-unqualified rig in traffic or near heavy equipment.

**G7 Outdoor sports (separate research track):** no cap substitution for a certified helmet, no hard/rigid insert beneath a ski/bike helmet, and no modification to shell/liner/retention. A candidate integration needs independent protection-impact/snag/retention and environmental qualification with protective-equipment specialists. This track is **not** cleared by EEG G0–G6.

## 7. Implementation milestones / proposed PR sequence

1. **This PR: v0.1 design + study plan (S0).** Research goals, risk boundaries, staged BOM, clock and validation questions; no executable hardware integration.
2. **PR-A: synthetic session contract.** Typed EEG/IMU/ECG/PPG/event/acoustic-feature manifests, explicit optionality, unit tests, privacy/lifecycle states, research-map owner and registry updates.
3. **PR-B: headform-only insert model.** Parametric neutral geometry plus one OpenSCAD/CadQuery backend; nonfunctional labelled placeholders and dimension checks; no wearable design claims.
4. **PR-C: synthetic acquisition adapters.** BrainFlow synthetic board, instrument-simulator feeds, session event recorder and LSL/XDF timing simulation; no raw human acquisition.
5. **PR-D: reproducible QC and counterfactual artifact tests.** Noise/dropout, interpolation and leakage adversarial fixtures.
6. **PR-E: reference-hardware feasibility proposal.** Exact vendor manuals and firmware pinned, electrical/skin/privacy checklist, headform/bench evidence and independently reviewed permission for limited self-study.
7. **PR-F: optional real-device connector** after separate review. Local-only, no agent exposure, documented safety and recovery behavior. Still no automatic evidence-level promotion.

## 8. Go/no-go decisions

- **Go on comfort only if:** independent fitting records do not show mechanical pinch, unsafe rigid interfaces or user discomfort; a pretty render alone fails.
- **Go on signal quality only if:** raw per-channel contact and known physiological contrast results can be reproduced and appropriately compared with a baseline.
- **Go on synchronization only if:** measured event latency/drift with a physical or similarly controlled time anchor meets a preregistered task-specific uncertainty budget.
- **Go on task models only if:** genuine held-out sessions outperform simple context/motion-only baselines with uncertainty and meaningful coverage.
- **Go on daily use only if:** separately qualified electrical, skin, thermal, mechanical, data-security and environmental aspects pass review.
- **Go on sports only after:** a distinct protective-equipment engineering and certification review; the EEG program grants no sport-helmet clearance.

## 9. Background references (for review; no implied license to copy)

- OpenBCI Cyton: https://docs.openbci.com/Cyton/CytonSpecs/
- OpenBCI dry headband: https://docs.openbci.com/AddOns/Headwear/HeadBand/
- BrainFlow: https://brainflow.readthedocs.io/en/stable/
- Lab Streaming Layer: https://labstreaminglayer.readthedocs.io/info/time_synchronization.html
- EEG-BIDS: https://bids-specification.readthedocs.io/en/stable/modality-specific-files/electroencephalography.html
- Polar BLE SDK H10 feature availability: https://github.com/polarofficial/polar-ble-sdk/blob/master/documentation/products/PolarH10.md
- 2025 mobile EEG motion-artifact review: https://pmc.ncbi.nlm.nih.gov/articles/PMC12473706/
- 2025 wearable dry-electrode review: https://pmc.ncbi.nlm.nih.gov/articles/PMC12389868/

**Outstanding decisions before a purchase:** which manufacturer-supported EEG baseline is available, actual inner cap dimensions/headform fit, electrode interface based on hair coverage, preferred compute host (laptop vs later phone), independently reviewed recording safety, and the first scientific experiment. No private biometric data should be committed to this repository.
