## V1.12.0 — S0 model-form sensitivity and observability diagnostics

- Perturb each illustrative stiffness/damping/travel parameter at two small finite-difference steps across up to four synthetic impact scenarios; preserve source-bound run fingerprints and check local derivative stability.
- Report per-parameter elasticity, weak influence and near-collinear parameter-pattern heuristics, without inferring structural or practical identifiability from them.
- Explicitly reject direct physical comparisons between scalar model peaks/neck-torque proxy and unreviewed 3D headform or upper-neck load-cell measurements.
- Add 16 adversarial tests, link model ownership in the scientific workflow registry, and run cross-platform sensitivity smoke in CI. No measured data, parameter fitting or protective claims.

## V1.11.0 — Unpaired/factorial nonhuman study-design preflight

- Add an offline, strict-schema, S0-only unpaired experiment review separate from the V1.10 matched-impact contract.
- Preserve all planned trials, including unacquired, failed and excluded observations, without reading raw signals or performing statistical inference.
- Report condition/stratum coverage, missing cells, order and day/headform/rig confounders, reused equipment and absent acquisition evidence.
- Ship a deliberately fictional six-trial example, new adversarial tests, workflow ownership and cross-platform CI smoke.
- Dataset metadata is not laboratory calibration, randomized assignment, preregistration chronology, physical model validation or helmet protection evidence.

## V1.10.0 — Matched impact study-design and pseudoreplication preflight

- Add a metadata-only, nonhuman S0 preflight to detect inappropriate pooling, reused acquisition identities, speed and apparatus mismatches, arm-order confounds, day/headform/rig clustering, and helmet reuse.
- Declare matched impact blocks as units and primary/secondary outcomes before effect estimation; preserve unresolved randomization, temporal preregistration, wear, calibration and generalizability blockers.
- Ship a completely fictional four-block demonstration and adversarial tests. Add module ownership to the workflow map and smoke-test in every OS/Python matrix job.
- Do not compute p-values, interpret physical signals, certify equipment or infer clinical/protective effects.

## V1.9.0 — Scientific workflow discoverability and owner-map audit

- Add stable START_HERE and SCIENTIFIC_ARCHITECTURE documents for researchers, contributors and agent users.
- Map eight research workflows to scientific questions, software readiness, S0 evidence ceiling, modules/tests, methods and related claims.
- Require every top-level scientific module to have a discoverable owner; adversarial tests reject evidence promotion, missing protocols, unsafe paths and unreviewed execution commands.
- Run the owner-map audit on every OS/Python CI matrix entry and align distribution metadata to version 1.9.0.
- Correct stale first-page README and historical architecture notes. No physical model validation, new human-data capability or automatic evidence promotion is introduced.

## V1.8.0 — Offline provider file inventory and byte consistency

- Review saved Dataverse metadata for a pinned released Borealis dataset version, selected headform trial file, measurement-specific README and repository README.
- Expose provider file IDs, size, restriction status, MD5/SHA metadata and local snapshot SHA-256; refuse wrong DOI, drafts, invalid checksums, duplicate selected files, unsafe names and malformed metadata.
- Compare a locally authorized original file's bytes with provider metadata **without parsing sensor samples**; retain explicit checksum mismatch and non-authenticity flags. MD5 matches never imply scientific provenance.
- Add adversarial tests, CI coverage and a laboratory-review guide; no third-party raw files or automatic downloads. All data remain S0.

## V1.7.0 — Explicit S0 measurement-mapping proposal

- Hash-bind clock and 3-axis physical quantity channels to the local CSV with exact per-quantity units, proper right-handed frame rotations and stable measurement reference points.
- Refuse reflections, skew, duplicate channels, non-monotonic/gapped clocks, changed source file/header and implicit head or neck point translations.
- Permit aggregate SI demonstrations only on declared synthetic fixtures; external nonhuman recordings remain review-only and S0.
- Include Draft 2020-12 JSON Schema, scientific mapping guide, adversarial regression tests, CI smoke and clean-wheel package resource check.

## V1.6.0 — Local nonhuman CSV structure and clock probe

- Add an opt-in, offline CSV inspection step for researcher-held, explicitly declared nonhuman/synthetic datasets, with file SHA-256, header hashes, row/column counts, and optional reviewed clock mapping.
- Refuse malformed/oversized/non-UTF8 inputs, duplicate headings, nonmonotonic timestamps and symlinked files; flag gaps and jitter without resampling or exposing raw samples.
- Label user-declared source identifiers as unverified, and preserve S0, file-level rights, calibration, coordinate frame, model-fit and medical/protective-performance blockers.
- Add 13 adversarial unit tests, synthetic-only CI smoke, and Borealis-oriented acquisition documentation without downloading or redistributing external measurements.

## V1.5 research source intake

- Catalog three new nonhuman biomechanics research leads and a direct NOCSAE faceguard standards landing page.
- Add source/ledger fingerprints and explicit file rights, instrument calibration, uncertainty and independent-laboratory blockers. No automatic data import or evidence-tier promotion.

## V1.4.0 — Outside-researcher reproduction challenge

- Fixed two-case, S0-only offline reproduction exercise with failure-preserving summary and no user-input code, URLs or real data.
- Replays bundled results against installed scientific kernels and checks exact expected tasks, not merely hashes.
- Adds clean-wheel challenge smoke, cross-platform CI, adversarial tests, and contributor feedback template. Does not claim actual outside independent reproduction or physical validation.

## V0.8.0 — Preregistered S0 waveform screen

- Added local, nonhuman paired full-window waveform metrics (peak/time, time-weighted RMS, integrals, normalized RMSE, correlation), provenance hashes and explicit per-modality alerts.
- Added immutable-by-convention analysis plan schema and exact-clock/no-posthoc-shifting quality gates; independent preregistration timing still requires external verification.
- Added always-blocked synthetic-to-measured model validation gate until calibrated 3D-to-1D mapping and a held-out protocol exist.
- Added 16 focused negative tests, CI smoke, research evidence registry and acquisition decision note. All example traces remain synthetic and S0.

## V0.7.0 — Local-only, nonhuman bench intake

- Added hash-bound acquisition profile for external nonhuman headform traces; declared rights and calibration remain independently unverified.
- Added single-pair descriptive peak/RMS resultant kinematic comparison, conservative declared-uncertainty bounds and explicit blockers.
- Added synthetic reference/candidate fixtures illustrating competing linear and angular responses; no physical evidence or clinical output.
- Added negative tests for tampering, clock drift, mismatched protocols and saturation, plus offline CI smoke.

## V0.5 research knowledge and retrieval layer

- Add offline S0 claims/sources registry with fail-closed structural audit.
- Stage only allowlisted Git `HEAD` source blobs for optional local XERJ indexing.
- Add transparent lexical search, twelve frozen navigation questions, Hit@5/MRR report and negative privacy/provenance tests.
- Add `AGENTS.md`, retrieval guide and CI smoke steps. XERJ remains an optional unqualified experiment, not a required runtime or scientific authority.

## V0.4.0: timebase accuracy and NONHUMAN bench-data contract (2026-10-23)
- Pre-step aligned head state, head acceleration, angular acceleration, mount displacement and neck torque on one timebase; avoids a silent 1-sample offset.
- Unrounded primary peak observables and opt-in full-precision synthetic audit traces, including a SHA-256 digest and explicit sample semantics.
- Corrected V0.2 and V0.3 numerical refinement comparisons to use unrounded primary peaks. Remaining status S0 even when gates pass.
- Strict offline, read-only NONHUMAN headform CSV+manifest structural validator. Rejects human origin, missing/duplicate columns, timestamp reversal, nonfinite data, undeclared frames and units. Flags gaps and reports content hashes.
- Added 6 dedicated regression tests; no live athlete data, calibration claims or helmet safety claims.

## V0.3.0: numerical cross-check (2026-10-23)
- Independently expressed RK4 solution of the same synthetic equations, including applied work, mechanical energy storage, progressive stop energy, and damping.
- Cross-solver report: 4 impact scenarios x 4 bounded design configurations, strict numerical-only pass/fail gates, source SHA-256s, case-level failures and conservative energy accounting.
- Analytical harmonic oscillator RK4 test, failure-injection regression tests, numerical-audit command, CI matrix integration.
- Still S0 synthetic and unvalidated; zero concussion, protection or hardware qualification claims.

# Changelog

## V0.2.0 (2026-10-23)

- Added bounded variable-step simulation for discretization sensitivity challenges.
- Added four-resolution numerical qualification CLI and localhost dashboard report. Passing does NOT change S0 evidence status.
- Added explicit synthetic-only multimodal channel and session validator with unit, timing-gap, amplitude finiteness and quality checks.
- Added local fixture generator and regression tests.
- Preserved V0.1 visualization, design-space sweep, reproducibility fingerprints, and fail-closed demo policy.

## V0.1.0

- First deterministic reduced-order impact workbench with synthetic EEG/EMG visualization.


## V0.6 (research metadata integration, no model validation)
- Added three curated external-reference catalogs: biomechanics, neural recording, evidence/qualification. All references are link-only and require separate license review.
- Added cross-linked S0 hypothesis gap register, metadata-only search, fixed integration benchmark and committed-HEAD-only per-domain staging for optional XERJ.
- Added negative permission/provenance tests and portable CLI/CI smoke checks. No real sensors, external models, standards text, human data, clinical scoring or S1 promotion.

## Proposed V1.1 agent-oriented research interoperability (unreleased)

- Add offline synthetic-only agent tasks, capability discovery, bundled JSON Schema and reproducible reports.
- Include source-code fingerprints, checksums and minimal RO-Crate 1.3 research metadata, without signing/authenticity claims.
- Reject human inputs, unknown operations, malformed commands, path tricks and tampered bundles in negative tests.
- Document future MCP, XERJ, neurOS and governed laboratory research workflows. No physical validation or S1 promotion.
