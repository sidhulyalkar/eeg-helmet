# NeuroCap sensor-layout tradeoffs: what should each contact actually measure?

**Status: research specification, S0 fictional coordinates; no measured montage or qualified recording.** This complements [the cap-and-ear assembly workbench](neurocap-assembly-workbench-v1.md) and [EEG headwear builder guide](eeg-headwear-build-guide.md). Synthetic site IDs in the lab must not be called 10–20 positions without measured anatomical registration.

## Design principle

The question is **not** "how many electrodes fit in a cap?" It is **which task-relevant source contrasts survive the complete acquisition chain, with measured artifact rates, across independent fits and days?** Headphones or a cap may provide a better user experience while reducing cortical topography. The tradeoff must be tested, not assumed.

### Candidate layout study

| Configuration | Nominal site families in the viewer | Testable strength | Main confound / risk | Default scientific interpretation |
|---|---|---|---|---|
| **D0: Ear only** | EL, ER abstract bilateral loop markers | Fast, minimally conspicuous wear; comparative auditory paradigms | Small differential voltages, jaw/face muscle, extremely sparse spatial baseline | Not sufficient to claim source localization, thought decoding or universal cognitive state |
| **D1: Daily hybrid** | FL/FR frontotemporal + EL/ER | Potential ease-of-contact plus lateral signal diversity | Blink/EOG and facial EMG, coupling changes under headphones | Evaluate repeated simple contrasts and artifact rejections, not a single focus score |
| **D2: Scalp research** | FL/FR, CL/CR and optionally RL/RR | Potentially improved topography, controlled motor/cognitive tasks | Hair-access, placement uncertainty, cap crown depth | Only compare after real positions, reference and fit are measured |
| **D3: Reference commercial cap** | Vendor-specific documented montage (not a fixture in viewer) | Independent signal-quality comparison and known protocols | Setup burden, differing equipment/montage | Baseline, not a universal ground truth |

**No design here defines a functional reference or bias circuit.** A "site" in a geometry illustration is not necessarily an independent differential EEG channel. Count the actual configured amplifier differential inputs only after a reviewed circuit manifest is available.

## Decide signals before fixing layout

### EOG / blink / eye movement

Forehead and frontotemporal contacts may measure strong ocular activity, which is useful for artifact tagging or intentional EOG interaction but can dominate an attempted cognitive EEG signal. For a game experiment, classify a gaze/eye event as a distinct physiological modality, **not a decoded mental decision**.

### Temporal and ear signals

Test auditory-evoked responses and within-person temporal features under controlled conditions, but account for jaw/face muscle activation, environmental sound and ear placement. Around-ear EEG has strong ergonomic appeal but limited spatial separation; using multiple close electrodes does not automatically give rich independent neural sources.

### Central sensorimotor activity

Candidate central scalp access could be useful for motor-related spectral contrasts, but the wearable must be shown to make reliable scalp contact through hair. Game-control movement and face/head muscles can contaminate these signals; test known motor conditions and EMG/IMU controls rather than assuming a movement decoder uses cortex.

### Posterior alpha and visual responses

Classic posterior alpha contrast is normally evaluated using posterior scalp sites. The current *fictional cap envelope* cannot establish access to occipital sites and does not include anatomical O1/O2. A separate, nonprotective posterior reference extension or commercial EEG cap may be needed. Do not treat low frontal-band alpha as a successful posterior alpha benchmark.

### Heart, motion, speech and task context

PPG and ECG should initially be independent commercial reference systems for physiological observables, not unreviewed extra contacts on the same custom analog chain. IMU and game-state events can explain many large artifacts and overt actions. Optional audio should be feature-only by default with explicit user recording controls. ECG, PPG and microphone streams do not improve EEG spatial resolution directly.

## Acquisition quality and clock contract

**When a properly reviewed nonhuman bench/electrical setup is eventually available**, measure:
- Amplifier input shorted noise spectrum, internal test-signal gain and ADC code scaling, drift and saturation.
- Channel-specific packet-loss/CRC/signed-data behavior and recovery after Wi-Fi disconnect or device reset.
- Movement/contact proxies from bench motion, dummy electrodes and controlled phantom inputs.
- Device sample counter and monotonic timestamps, not merely host receipt time.
- Calibration of mapping between EEG ADC source clock and game presentation/physical stimulus timing, including uncertainty and clock drift.
- Actual referencing/bias configuration, lead-off status and manufacturer instructions.
- Separate audio-ON/OFF tests to quantify switching/EM interference from headphones.

**Only after appropriate human-use electrical/material review** should separately approved human experiments compare electrode assemblies under eyes-open/closed, speech, facial movement, seated gaming and controlled movement. Preserve raw recordings and unusable segments; report accepted intervals, independent fitting repeats and confidence. Do not let an ICA or a foundation-model embedding stand in for a measured physiological contrast.

## Quantify information yield, not a marketing score

A candidate observation metric is

    usable_task_aligned_seconds =
      total_recorded_seconds
      - invalid_acquisition_seconds
      - unverified_sync_seconds
      - rejected_artifact_seconds
      - intervals_without_required_task_context

These sets may overlap: compute the **duration of their union** or a logically defined per-window mask, not independent subtraction that double-counts. Preserve both inclusion and exclusion reasons.

For scientific inference compare held-out session/day performance from:
1. Game state and actions only.
2. Video + IMU + EOG/EMG artifact controls.
3. EEG-only quality-gated baselines.
4. EEG + other streams.
5. Optional pretrained EEG encoders after standard baseline reproducibility.

A predictive improvement conditioned on game state can support the utility of recorded features, **not** identify private intentions or unique cortical sources. A meaningful result needs confidence intervals and failures.

## Measurement plan before 3D fitting goes further

Start with three nonhuman reference headform sizes (declared dimensions, not population anthropometry), three independent assemblies per size, and multiple cap inner geometries. Record:
- Ellipsoid-to-real headform deviation and cap clearance via independently documented measurement method.
- Candidate nominal site variability with measured fiducials, not inferred 10–20 nomenclature.
- Ear module relative placement variation, glasses clearance and headphone interference on mannequins.
- Electrode-placeholder displacement during headform-only translational/rotational movement; note fixture limitations.
- Buckling, breakage, removable components, cable snag, deflection under controlled instrumented nonhuman loads.
- Assembly/removal time and cleaning accessibility for *noncontact* modules.

Do not invent universal safe electrode pressure, thermal limits or acceptable skin-wear duration. These require qualified applicable standards review and real evidence, and they cannot be inferred from this visual mock-up.

## Why these designs can coexist in a single repo

The public lightweight S0 model owns **geometric declarations and reproducibility**. The optional NeuroDAQ hardware track owns bench electrical source/version/driver evaluation. A separately reviewed acquisition component will eventually own private measured physiological data outside Git. The gameplay observatory owns game-event semantics and timestamp uncertainty. The same typed manifest should link these without mixing distinct evidence levels.

**Next decision point:** only design detailed real contact-cartridge geometry once headform fit tests establish which nominal sites are mechanically accessible and a safety review defines allowable materials/contact construction. Keep the wearable comparison as a hypothesis until that point.
