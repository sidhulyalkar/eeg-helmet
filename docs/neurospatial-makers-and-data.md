# NeuroSpatial community fabrication and longitudinal data charter

**This document is a plan, not an approved electrical design, clinical recording protocol, manufacturing package or data collection authorization.**

## Community entry paths

1. **Software-only:** run S0 inverse benchmarks locally; no headset or participants required.
2. **Existing validated EEG device:** use its own manufacturer-approved power and acquisition design; record locally through a supported driver, preserve units, hardware sampling clock, reference scheme, montage and firmware. This repository does not yet implement that driver.
3. **Research lab:** contribute audited electrode geometry, phantom validations and independently approved human research protocols.
4. **Maker hardware (future):** contribute OpenSCAD/STEP designs and CAD fit studies for a headwear *fixture* without electrical contacts, then seek independent review before pursuing on-body electrical recording.

## Release gates for a wearable

- **H0 design-only:** reproducible CAD, BOM including manufacturers and tolerances, printable fit coupons, mechanical drawings, explicit nonfunctional warning.
- **H1 benchtop electrical:** approved battery-only isolation architecture, measurement front end, leakage/current-limiting analyses, fault-tree testing, EMI evaluation and independent review. Do **not** connect DIY electrodes or circuitry to a person, or connect on-body equipment to unsafe mains/USB power, on the basis of this repo.
- **H2 skin-contact study:** qualified oversight of biocompatibility, wear pressure, cleaning, contact stability and comfort.
- **H3 research acquisition:** approved human study, consent, protection and calibration; never infer commercial or clinical clearance.

No hardware release should promise that a custom 3D-printable electrode makes recording safe. Open hardware is not automatically safe hardware.

## Private-by-default personal experiments

A personal research notebook should store raw signals and diaries on the participant's own machine. Nothing in the current code collects, processes, uploads or anonymizes real human data.

Future data contracts should use EEG-BIDS where relevant and maintain:

- Pseudonymous participant ID (never name/email/phone), separate consent record and explicit per-purpose sharing scopes.
- Device, firmware, channel layout, units, reference electrode, impedance/contact metadata, timestamp source, packet loss and synchronization uncertainties.
- Recording environment, movement/EOG/EMG nuisance measurements, task instructions and behavioral ground truth.
- Source-model assumptions, uncertainty estimates, calibration provenance, excluded intervals and negative findings.
- Local deletion controls and independent opt-in for any contribution. Data should not be submitted in GitHub issues, attachments, CI logs or PR fixtures.
- A separate, reviewed data-release procedure that assesses re-identification risks. Pseudonymization is not anonymization; raw EEG and behavioral diaries may contain sensitive signals.

**Never commit actual human EEG, subject MRI, video, consent forms, raw speech, health data or person-identifying diaries to this public repository.**

## Useful everyday interventions: an evidence-first plan

The platform may *investigate* attention, workload, fatigue, task switching and personally chosen routines. Do not claim the wearable reads unconstrained thoughts, emotions or intentions.

Start with observational associations and **behavior-only** baselines. For any proposed feedback intervention, predefine:

- One participant-selected, measurable outcome and a clinically appropriate exclusion/stop policy where applicable.
- A model trained on earlier sessions, assessed on held-out **future days**, and compared with simple non-neural features.
- Calibrated confidence and an abstention path when signal/contact quality is poor.
- Randomized intervention versus control/no-feedback decision points, including side effects and participant choice to stop.
- No hidden nudging, coercive workplace/sports use, or automated medical, hiring, or academic decisions.

Open source the **methods, schemas, tests and reproducible aggregate reports** by default. Share personal recordings only with informed, granular participant permission and independent governance.
