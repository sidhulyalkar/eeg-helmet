# Building an EEG headwear research prototype

**Audience:** students, makers, research engineers and laboratories exploring nonclinical scalp EEG. **Status:** educational design guide, not a verified build, validated sensor, certified helmet, or permission to collect human data. Read [the evidence contract](research-contract.md) and [the scientific architecture](SCIENTIFIC_ARCHITECTURE.md) first.

This guide deliberately separates two projects that share a head-shaped form factor but **not** the same scientific claim:

- **EEG headwear:** fit, electrode placement, contact stability, signal acquisition and reproducible neural-data methods.
- **Protective sports helmet:** impact attenuation, materials, shell integrity, retention, test standards and validation by qualified labs.

**Never attach this project's experimental electrode hardware to a certified protective helmet, nor drill, cut, fasten or reconfigure its shell, liner or retention system.** A prototype EEG frame does not provide impact protection. Helmet mechanics simulations in NeuroShield are synthetic and cannot establish a safe protective design.

## What is already available?

NeuroShield currently includes synthetic EEG/EMG event examples, timing/session contracts, mechanical toy models, read-only knowledge search and evidence registries. It does **not** ship a usable wearable, amplifier electronics, validated electrodes, real EEG streaming interface or approved human-recording process. The proposed NeuroSpatial Open inverse-EEG research track is separately under review in [PR #7](https://github.com/sidhulyalkar/eeg-helmet/pull/7); its spatial mixing examples, if merged, will remain synthetic and do not recover a person's thoughts.

The most useful first contribution is a **benchmarkable, modular EEG-headwear *research* specification**, not a file advertised as “print this safe EEG helmet”.

## Choose a reproducible reference experiment

| Track | Goal | First artifact | Still missing |
| --- | --- | --- | --- |
| A: digital-only | Learn montage coordinates, amplifier metadata, artifact and timing contracts without touching a subject | synthetic session + machine-readable electrode map | Any physical verification |
| B: passive mechanical mock-up | Explore size range and mounting concepts on mannequins/headforms only | parametric CAD, STEP/STL preview, fit log | Biocompatibility, load/contact and human-use review |
| C: existing research headwear | Study the ecosystem using vendor-supported, unmodified EEG cap/headset and approved acquisition hardware | local signal-quality protocol, calibration and acquisition metadata | Independent scientific feasibility and governance |
| D: novel electrodes/electronics | Design new skin contacts or amplifier circuitry | design history, safety/hazard analysis and bench-only test plan | Qualified electrical/biocompatibility review before any human connection |
| E: protective helmet integration | Evaluate EEG within impact-rated equipment | **research proposal only** | Independent protective-equipment engineering, certification pathway and ethics approvals |

The recommended order is **A → B → C**, with D and E explicitly separate expert-led efforts. A low-channel-count baseline with honest electrode quality and event timing is more informative than a dense unvalidated array.

## System decomposition

```text
[declared head surface and anatomical landmarks]
           |
[nonprotective frame/cap + indexed electrode sites]
           |
[reference / ground / individual EEG contacts]
           |
[reviewed acquisition hardware + electrical safety boundary]
           |
[raw time series + amplifier-specific metadata]
           |
[clock-offset and marker provenance]
           |
[quality-control report + artifact annotations]
           |
[local governed analysis + data / consent policies]
```

For a *real* device, safety review precedes connection to any person. The diagram is a research decomposition, **not** wiring instructions. Do not connect experimental EEG circuits to mains-powered equipment or to people before appropriate qualified review and isolation precautions.

### Interoperable design manifest

Record these fields from the first mock-up, even when values are `not_measured`:

| Field | Why it is required |
| --- | --- |
| Design ID, revision, CAD engine/version, source license | Distinguishes reproducible geometry from screenshots |
| Intended context of use | Avoids confusing resting EEG, sport motion and clinical use |
| Physical units, geometry axis conventions, reference headform and landmark registration | Prevents coordinate-system and scale errors |
| Electrode labels and intended international 10-20/10-10 references | Reproducible nominal sites, **not** measured scalp positions |
| Contact approach (wet, saline, dry) and replaceable interface | Hair and scalp coupling are part of the mechanical design |
| Cable routing, strain relief, exposed-contact and pinch hazards | Identifies design risks, not evidence of safety |
| Amplifier identity, sample rate, units, reference and ground conventions | Prevents accidentally comparing incompatible EEG data |
| Channel map, clock domain, event timing origin and clock-correction method | Enables latency/jitter and event-locking audits |
| Fit/contact notes covering different head sizes, hair textures and accessibility | Avoids tuning the headwear to only one head |
| Data permissions, retention class and whether the output is synthetic | Determines whether indexing, sharing or analysis is allowed |

Use **millimeters for CAD geometry** and state transforms explicitly when exporting meters for analysis. An idealized montage is an *initial design target*, not an observed electrode location; physical digitization or a validated measurement procedure is needed for subject-specific electrode positions.

### First measurements to preregister (when lawful and reviewed)

**Mechanical headform-only:** electrode location deviations from declared landmarks, adjustment range, mass distribution, elastic deflection, cable accessibility, point contact force (with suitable instruments), frame slip under nonhuman motion, replacement ease and repeatability across separate assemblies. Report minimum/maximum and failures, not only a single good fit. No “safe contact pressure” threshold is declared here.

**Electrical bench-only:** documented phantom/test-signal behavior, input-referred noise under declared measurement conditions, cross-channel interference, dropped samples, power interruption, packet loss and synthetic timestamp/event latency. Do not treat a noisy signal simulation as a real biomedical safety assessment.

**Later ethics-approved human feasibility only:** contact quality and variability across hair, sessions and movement; standardized simple contrast checks (e.g., eyes-open vs eyes-closed alpha modulation) with explicit negative controls; event-marker timing and clock uncertainty; hardware and human comfort/adverse-event logs. Alpha changes, blink detection and high classifier accuracy alone do **not** establish useful BCI performance, source localization or psychological-state decoding.

## How to design a useful research comparison

Predeclare at least one *baseline* (existing vendor cap or reference mechanical mock-up) and one candidate. Freeze electrode count, target placement, electrode material/interface, motion regime, acquisition chain and sample rate before comparing. Attribute improvements separately to fit, electrical contact, filtering or decoding. Test multiple **independent fits/sessions/headforms**, not just many time windows of the same session. Preserve cases with poor hair contact, motion contamination or failed acquisition. Never claim that a source reconstruction method has recovered neural detail merely because its forward-predicted scalp voltages match.

Suggested initial evaluation dimensions (not safety certifications): completeness of declared metadata; montage placement error under a declared headform registration; mechanical repeatability; per-channel missingness; frequency-specific artifact susceptibility; measured trigger latency and drift (when instrumentation exists); and setup burden. Publish measurement methods, uncertainties, conditions and negative controls alongside every result.

## Reproducible starter path today

These are software-only operations on **synthetic** examples:

```bash
python -m pip install -e .
python -m neuroshield synthetic-session --out ../session-SYNTHETIC.json
python -m neuroshield validate-session ../session-SYNTHETIC.json
python -m neuroshield.research_map show synthetic-neural-events
python -m neuroshield.research_map audit --root .
python -m unittest discover -s tests -v
```

Read [CAD and retrieval toolchain](cad-and-retrieval-toolchain.md) for Zoo, FreeCAD, CadQuery, XERJ and governed source search. A future complete maker example should provide a **manifest + editable parametric source + nonfunctional geometry preview + all validation failures**, not only an STL.

## Decisions we deliberately do not automate

- No unqualified medical, concussion, cognitive or emotional inference from EEG.
- No agent-selected acquisition from people, cloud upload, unsafe electrical control, active stimulation or modification of protective equipment.
- No indexing of human recordings, demographic markers, unpublished lab notes, consent documents or proprietary CAD into XERJ or a cloud CAD service by default.
- No claims of electrode biocompatibility, IEC compliance, sport-helmet protection or clinical safety from a render, CAD analysis, software unit test or LLM suggestion.

## Primary references for future builders

These links are learning resources, **not blanket permission to copy files or proof of a specific design**. Check each version and license before reuse.

- [OpenBCI EEG setup and headwear](https://docs.openbci.com/GettingStarted/Biosensing-Setups/EEGSetup/) and [Ultracortex Mark IV documentation](https://docs.openbci.com/AddOns/Headwear/MarkIV/). A useful mechanical reference, not an endorsement of a custom modification.
- [OpenBCI Ultracortex CAD repository](https://github.com/OpenBCI/Ultracortex). Review the **actual asset-level license and revision** before copying geometry.
- [BrainFlow documented board abstraction and synthetic board](https://brainflow.readthedocs.io/en/stable/index.html). Good candidate for a future optional acquisition adapter, not an existing integration.
- [MNE-Python montage definitions](https://mne.tools/stable/generated/mne.channels.make_standard_montage.html). Do not assume template sites equal individually digitized coordinates.
- [EEG-BIDS](https://bids-specification.readthedocs.io/en/stable/modality-specific-files/electroencephalography.html) for coordinate-system and recording metadata requirements; pin the exact specification release in an actual experiment.
- [Lab Streaming Layer time synchronization](https://labstreaminglayer.readthedocs.io/info/time_synchronization.html) and XDF for event/clock provenance.
- [NeuroShield's metadata-only neural catalog](../knowledge/corpora/neural.json) and [evidence contract](research-contract.md).

## First external-contributor challenge

Can someone unfamiliar with this repository (1) reproduce the synthetic EEG session, (2) describe the limits of a montage without individualized coordinates, (3) build or inspect a **headform-only**, nonfunctional electrode-holder concept in a CAD tool of their choice, and (4) submit its editable sources, manifest, negative checks and tool versions without a private recording? Track setup time, blocked steps and unambiguous failures. That is a meaningful public contribution even before a complete headset exists.
