# Gameplay Decision Observatory: event-first multimodal research (proposal v0.1)

**Status:** proposal and synthetic-only software plan, 2026-11-22. Not a completed integration, approved human study, verified acquisition path or medical/psychological decoder. The public NeuroShield repository remains S0. See `AGENTS.md`, `docs/research-contract.md`, and `docs/eeg-headwear-build-guide.md`. This research path is complementary to draft NeuroCap headwear PR #39, not a change to helmet safety or validation claims.

## Thesis

A high-fidelity game-event stream, synchronized inputs, game visual observations and optional professionally reviewed physiological streams can support within-person empirical analyses of strategy, attention, adaptation and motor decision-making *without requiring the player to annotate every mental event*. Behavior, game mechanics and neural recordings provide different types of evidence: neither observed inputs nor scalp EEG establish private intention or thought content.

**Priority:** make a useful instrumented game benchmark *without EEG first*. Then add manufacturer-supported raw EEG only when the exact device provides sample timestamps, reference/ground/montage, documented SDK/data rights and independently reviewable quality metadata.

## 1. Data tiers and collection boundaries

| Tier | Source | Measured vs inferred | Main limitation |
| --- | --- | --- | --- |
| T0 | In-app game plugin; first-party instrumented simulation | Direct game state/events with engine timestamps | Available only when developer exposes state / offline legal mods |
| T1 | Input logger + focused screen/video capture | Observed buttons, controller state and rendered pixels | Button != intended action; no hidden state; clock mapping |
| T2 | Local scene analysis/OCR/VLM | Inferred context, enemy appearance, damage, UI, scene transitions | Errors, missed frames, uncertain or biased labels |
| T3 | ActivityWatch watcher | App/window focus and AFK intervals | No fine-grained game decisions |
| T4 | Optional physiological streams | Measured EEG/EOG/EMG, PPG/ECG and IMU | Artifacts, different device clock domains and safety/privacy |
| T5 | Optional OpenClaw agent/logbook | Post-hoc summaries over *allowlisted derived features* | Periodic snapshots too coarse for combat; model inference may be wrong; cloud exfiltration risk |

**Recommended collector order:** first-party game telemetry > window-scoped capture + input events > explicit local visual inference > physiology > optional agent summarization.

ActivityWatch: https://activitywatch.net/ and its extensible local REST watchers.

OpenAdapt Capture (2026-11-19 release notes): https://openadapt.ai/platform/capture; scoped application video and timestamped key/mouse events. Its generic desktop mode can record typed text: ***for our project, disable or discard text/clipboard capture and reject sensitive-app contexts***; explicitly record only game-input button identities plus state changes.

OpenClaw Logbook: https://docs.openclaw.ai/plugins/logbook; periodic snapshots + post-hoc summaries, not an authoritative game event stream. Configure read-only allowlisted sessions and local models; deny screen control and private directories to agents. OpenClaw should not receive raw physiological data, microphone recordings or general desktop secrets by default.

## 2. First pilot game ladder

**Pilot A: instrumented first-party 3D world/mini-game (controlled baseline).** If user controls the game's code, emit typed events for state, visibility, opponent state, player position, attack cue, action opportunities, decisions, outcomes, death, checkpoint, traversal and restart. This supports ground truth and independently measured input timings.

**Pilot B: Hollow Knight or Silksong (when a version-compatible, permitted telemetry adapter exists).** Existing HKViz mod provides a reference for detailed player movement / progression but uploads recordings to its own service; review its code, rights, data-transfer behavior and game-version compatibility before reuse. Build an independent local-only telemetry writer if permitted; otherwise rely on pixels and input. Do not assume the mod is a safe local-first data sink.

**Pilot C: Elden Ring/open-world third-party game.** Start with external video/inputs only, no memory scraping, game injection or anti-cheat bypass, especially online. Extract only confidently observable game events; do not claim scene reconstruction provides complete world state. Offline game mods, if ever considered, require game EULA, permissions, integrity and safety review.

## 3. Canonical session model (proposed, not implemented)

One session has:
- `session_id`, `game_id`, `game_version`, `source_rights`, `protocol_id`, `study_design_version`, `consent_scope`, `device_manifest`, `capture_process_allowlist`, `privacy_scope`, and reproducibility hashes;
- video asset table (capture codec, FPS actual and nominal, frame PTS/DTS, dropped-frame count, audio capture controls);
- `game_event` table: `event_id`, `event_type`, `game_state_ref` (only for T0), `t_source`, `t_session`, `sigma_t`, `detector_origin`, `confidence`, `raw_evidence_ref`, `observable_vs_inferred`, `abstained`, and provenance;
- action table: device and mapping, button/controller axes, press/release interval, raw event time, resulting game action when observed, uncertain/unobserved outcomes;
- optional biosignal segments: device sample counters, reference graph, physical electrode metadata, measured clock models, raw-quality flags, artifact mask, units and offline data-rights classification;
- event-to-trial segmentation: encounter ID, opportunity set when *known*, event context, previous encounters, known outcomes;
- immutable local-only raw data; derived feature exports separated from source recording, no EEG or screenshots in public Git/XERJ/agents by default.

**Time map:** per source `t_session = a * t_source + b` estimated with physical or software calibration anchors; preserve original device timestamps and actual uncertainty. Host arrival timestamps are not valid EEG acquisition times. For ERP-like analysis verify end-to-end event timing with external stimulus photodiode/audio-loopback or suitable hardware bench test. Report unmeasured/unverified latency as such.

## 4. Candidate scientific questions and controls

### RQ1: response to uncertain or surprising encounters
Use a priori operational definitions: new visual enemy, new attack animation, unexpected health loss, cue transition. These are **observed surprise proxies**, not subjective surprise/fear. Estimate action onset, speed/direction change and pre/post autonomic/EEG features when quality passes. Compare repeated encounter instances; include actual stimulus visibility and elapsed play time.

### RQ2: learning across repeated failure
Mark identical boss/opponent attempts from state IDs when available; measure changes in defensive response timing, attack opportunities, errors, progression and strategy shifts. Control for enemy phase, weapon/loadout, health, familiarity and task difficulty. Avoid cherry-picking best attempts.

### RQ3: exploration vs exploitation
Require an explicitly modelled observable action set and information/reward structure in a custom game. In uncontrolled open-world footage, exploration scores are heuristics, not proof of internal preference. Compare same participant across declared conditions using a fitted behavioral model and holdout episodes.

### RQ4: EEG added value beyond behavior/context
Evaluate against: task baseline, game-state-only, input-only, video-only, IMU/EOG/muscle artifacts, EEG-only, multimodal. Report quality-accepted coverage, abstention, F1/balanced accuracy/calibration when class labels exist, time-to-event errors, and day/encounter holdout splits. No adjacent overlapping windows across train/test. Distinguish behavior decoding from neural signal contribution.

### Computational models
- Initial transparent state-based descriptive reports and event-triggered averages.
- Action policy `P(a_t | observable state_t, history_t, subject parameters)`; compare hidden Markov switching strategy, Bayesian inverse planning/POMDP and simpler imitation baselines only on games with adequately known state/action sets.
- Treat 'intent', 'creativity', 'risk tolerance', 'stress' and 'personality' as *hypotheses or user-labeled constructs*, not EEG-decoded truth.
- Raw EEG representation modeling only after demonstrating stable event-related effects and access to true raw signals.

## 5. Prospective experiment design

**Phase 0, software-only:** fixed synthetic sessions with deterministic events, video clock/frame slips, controller events, fake physiological channels, confidence flags and adversarial errors. Unit tests reject double-counted events, clocks moved backward, absent origin, missing acquisition source or private-data writes. No human data.

**Phase 1, behavior-only (~5–10 sessions as a feasibility plan, no statistical guarantees):** controlled instrumented game and isolated game-only capture. Quantify event precision/recall on an independently reviewed, sampled video reference; game state ground truth where available; input logger event latency and screen drift; privacy guard effectiveness.

**Phase 2, commercial physiological reference:** after qualified safety/privacy review, add a vendor-supported raw-stream EEG device, head motion and optional separately supported heart sensor. Check artifact incidence, communication dropouts, comfortable wear and task-related raw-signal contrasts. No untested custom skin-connected circuits.

**Phase 3, event-locked tests:** preregister event classes, holdout sessions, neural/artifact feature windows, baseline comparators and nonindependent sample unit; compare with / without physiological streams.

**Phase 4, longitudinal and adaptive gameplay:** only after evidence of additional neural predictive information and ethical assessment; explore optional game challenge adaptations with explicit user control and no exploitative steering.

## 6. Hardware decision gate

**Do not choose consumer Neurable One for raw EEG research until written confirmation** of streaming/exporting **per-channel raw voltage data** (not focus-score CSV), timestamps/sample counters, electrode reference/montage, sample rate/gain, access to signal-quality measures, offline/local rights, SDK licensing and device availability. Neurable One advertises CSV export but **no developer SDK at launch**, and says raw data are processed on its servers. Neurable research/dev kit is a different access pathway.

Alternatives to evaluate:
- IDUN Guardian 4: published Python SDK, raw/filtered EEG and IMU support, paid offline option; verify shipping, SDK, actual device, cost and data terms.
- BrainBit EEG Headphones: advertises 4-channel raw EEG plus an SDK; request a sample recording/SDK before committing; different electrodes and audio design from Neurable.
- OpenBCI or comparable vendor-supported cap: best baseline for electrode coverage and referenced event timing, but poor all-day convenience; treat as research comparator.

Neurable One is potentially fine as a consumer audio and derived-metric side study, not as the sole reproducible raw-data acquisition dependency.

## 7. Privacy and OpenClaw security

Use explicit manual arming **only when selected game/process window is foreground**, auto-stop on app change, clear recording indicator, local encrypted file store, retention timer, easy delete and event-level redaction. Never collect passwords, chats, other people’s microphones or generic key text. Physical input identity can be logged only in-game and must not capture sensitive text. A general-purpose agent with remote tools should not be granted continuous screen or unrestricted local-recording access. Keep the data collector deterministic and separate; agent requests must operate on reviewed summaries, with a log of exactly what was shared.

## 8. Planned minimal PR sequence (not implemented)

1. docs/spec + ethics/evidence review (this PR).
2. typed synthetic `GameEvent`, `InputEvent`, `FrameObservation`, `ClockTransform` contracts, with explicit confidence and unknown state;
3. simulated window-scoped capture + input event replay and no-human-data CI;
4. independent game-adapter integration/controlled reference ground truth, local recording only;
5. raw-biosignal manifest and clock QCs on phantom/synthetic data, no human capture in default NeuroShield core;
6. independent review of commercial EEG stream/consent/privacy, then optional external local acquisition component and benchmark report;
7. offline behavior-first decoder and error analysis; optional gated agent summaries on derived records.

## 9. Relevant evidence (for further review)
- Neurable One: https://www.neurable.com/products/neurable-one and SDK/CSV caveat https://checkout.neurable.com/
- Neurable development kit: https://www.neurable.com/dev-kit
- OpenClaw Logbook: https://docs.openclaw.ai/plugins/logbook
- ActivityWatch: https://activitywatch.net/
- OpenAdapt Capture: https://openadapt.ai/platform/capture
- IDUN Guardian SDK: https://sdk-docs.idunguardian.com/
- BrainBit EEG headphones SDK: https://brainbit.com/hardware-solutions/brainbit-headphones/
- MultiPENG: https://www.cs.sfu.ca/~mhefeeda/Papers/dd25_playerEngagementDataset.pdf (2025, 39 players; six synchronized streams)
- AMuCS: https://pmc.ncbi.nlm.nih.gov/articles/PMC12311033/
- HKViz: https://github.com/hkviz/hkviz-mod (automatic uploads require scrutiny)

**Evidence ceiling:** no conclusions about neural decoding, human thought, game decision motive, safety or device validity follow from this document alone.
