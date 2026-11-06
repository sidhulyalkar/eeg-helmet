# Open EEG ecosystem: comparative landscape and contributor blueprint

**Status:** Maintainer research and proposed architecture, 2026-11-06. **Evidence ceiling: S0**. No real EEG acquisition, approved hardware design, calibrated physical measurements, medical claims or proof of a human-facing EEG headset is implied.

For an executable first step, run `python -m neuroshield.ecosystem audit --root .`; the machine-readable, **metadata-only** source index is [knowledge/ecosystem/projects.json](../knowledge/ecosystem/projects.json). This is *not* a complete survey or a guarantee of current upstream maintenance, licensing, safety or product claims. Links and authored descriptions were assembled for comparison; actual file-level licenses and reuse terms remain **pending review**.

## Mission: an open, reproducible environment, not another isolated headset

A global contributor should be able to **learn, inspect, prototype, challenge, reproduce and responsibly improve** EEG headwear, from a laptop with no equipment through to qualified academic or industrial laboratories. New entrants should not be forced to purchase a specific headset, GPU, cloud CAD subscription or proprietary data source.

This workbench has two **separate** scientific tracks:
1. **Nonclinical EEG research headwear**: standalone caps or frames, electrode positioning, contact stability, acquisition metadata, signal QA, visualization and BCI methods.
2. **Helmet/head-neck mechanics**: synthetic biomechanics and eventual independent nonhuman headform qualification. These simulations do not support protective-performance claims.

Do **not** retrofit, drill, attach novel electronics to or modify impact-certified protective helmets; doing so can compromise safety and certification. The shared word "helmet" is not evidence these systems can be integrated.

### Survey of external reference projects

| Project / upstream | What to learn, not copy automatically | Our potential complement |
| --- | --- | --- |
| [OpenBCI Ultracortex](https://github.com/OpenBCI/Ultracortex) | 3D-printable modular electrode mounts and user-facing assembly documentation | Headform-specific, parameterized electrode layout and independently tested geometry exports |
| [OpenBCI hardware docs](https://docs.openbci.com/ForDevelopers/HardwareDevelopment/) | Board architecture, known channels, connector conventions and historical schematics | Safe comparative documentation and device-specific acquisition schemas; never infer electrical safety |
| [HackEEG](https://github.com/starcat-io/hackeeg-shield), [FreeEEG](https://github.com/eric5512/FreeEEG) | Alternative ADS1299 electronics and documented prototype boundaries | Evidence-first electronics risk and calibration review, **not** human-use wiring tutorials |
| [PiEEG](https://docs.pieeg.com/about/community/) | Open acquisition software and accessible Raspberry Pi integrations; upstream says hardware design is proprietary | Explicit software-vs-hardware openness labeling and interoperability tests |
| [OpenEarable ExG](https://www.dmz.teco.edu/research/openearable_exg/) | Open research for ear-based biopotential acquisition including EEG/EMG/EOG | Distinguish ear-EEG spatial sensitivity and practical form factors from scalp electrode arrays |
| [Dry-electrode review](https://pmc.ncbi.nlm.nih.gov/articles/PMC12389868/), [field quality methods](https://www.eneuro.org/content/12/7/ENEURO.0006-25.2025) | Contact materials, hairstyles, movement artifacts, power noise and field research workflows | Make diverse-headform repeatability, setup time, contact failures and equitable access first-class outcomes |
| [BrainFlow](https://brainflow.readthedocs.io/en/stable/) | Hardware-independent API, synthetic board, multiple supported devices | Optional adapter built on a synthetic board first, manifest/QC contract shared across devices |
| [LSL](https://labstreaminglayer.readthedocs.io/), [Timeflux](https://timeflux.io/) | Timing-aware streams and real-time processing graphs | Measurable drift/latency budget, marker provenance and failure-preserving replay |
| [MNE-Python](https://mne.tools/stable/index.html), [EEGLAB](https://sccn.ucsd.edu/eeglab/) | Established EEG preprocessing, montage and artifact handling | Curated standard analyses, evidence-linked negative controls, educational visualization |
| [MNE-BIDS](https://github.com/mne-tools/mne-bids), [EEG-BIDS](https://bids-specification.readthedocs.io/en/stable/modality-specific-files/electroencephalography.html) | Portable raw data and coordinate system conventions | A minimal, BIDS-aligned and falsifiable metadata contract; not premature full raw-data storage |
| [MOABB](https://github.com/NeuroTechX/moabb), [Braindecode](https://braindecode.org/stable/), [pyRiemann](https://pyriemann.readthedocs.io/en/latest/) | Benchmarked decoding and diverse baselines | Cross-device/session protocols, no leakage, honest abstention and failure counts |
| [OpenNeuro](https://openneuro.org/) | BIDS datasets and versioned scientific distribution | Links and provenance only; raw human datasets remain outside this repository |
| [NeuroTechX](https://www.neurotechx.org/) | International open community, mentorship and benchmarks | Global contributor onboarding, independent reproduction challenges, multilingual accessibility |
| [FreeCAD](https://www.freecad.org/), [CadQuery](https://cadquery.readthedocs.io/en/latest/), [Zoo KCL](https://zoo.dev/) | Editable parametric headform geometry; Zoo is hosted and optional | Geometry protocol independent of backend, pin engine versions and compare exports |
| [XERJ](https://github.com/xerj-org/xerj) | Source-grounded search and optional agent retrieval | Approved-source catalog indexing, measured retrieval gains, explicit permission boundaries |

These references expose two research directions a generic 10-20 helmet misses: **ear-based ExG** as a separate low-profile spatially constrained sensing geometry, and **global field usability** where hair variation, motion, setup training and line noise can dominate nominal amplifier specifications. Neither should be treated as directly comparable to a full-scalp EEG cap without controlled measurements.

**Not all listed projects are open hardware or entirely open source.** Some are a public data service, community, standard or hosted tool. Even apparently permissive upstream repositories can contain separate CAD, firmware, library, figure or dataset licenses. Direct links are **not** reuse licenses.

A good first contributor task is to check one upstream project's *current* release and asset-specific terms, submit a reproducible source-version card and flag any unsupported compatibility claims. Do not replicate upstream implementation unless a benchmark proves a missing feature.

## The eight research and product layers

```text
 LEARN / EDUCATE / OPEN QUESTIONS / CONTRIBUTOR DISCOVERY
                         |
         VERSIONED PROJECTS + EVIDENCE REGISTRY
                         |
                SCIENTIFIC WORKFLOWS
  +----------------------+---------------------+
  | Head geometry        | Synthetic sensing   |
  | CAD + montage target | Phantom + artifacts |
  +-----------+----------+----------+----------+
              |                     |
    calibration/QC contracts   optional analysis adapters
              |                     |
             reproducible runs + RO-Crate reports
                         |
               independent verification
                         |
       qualified nonhuman or governed studies
```

1. **Learning and navigation.** First five minutes must work offline, with no EEG device or AI account. Every public example declares what it demonstrates and what it **cannot** demonstrate.
2. **Head geometry and anthropometry.** Editable nonprotective headform geometry, units/frames, fiducials, reproducible adjustments, collision/clearance reports, and accessibility notes. A standard 10-20 layout is a nominal target, **not** a measured individual scalp montage.
3. **Electrode/material interface.** Document contact mechanisms, replaceable interfaces, hair and skin variation, cleaning/material hazards, strain relief and missing contact data. Do not invent universal contact pressure thresholds.
4. **Acquisition contracts.** A device-neutral typed channel and hardware manifest, with reference/ground definitions, gain, rates, resolution, clock domains, versioned firmware and self-declared calibration. **No** production human acquisition until qualified electrical safety and study governance exists.
5. **Signal quality and time synchronization.** Phantom-injected signals first; missingness, dropouts, saturation, line noise, artifacts, reference dependence, drift, timestamp uncertainty, and recovery behavior. Do not claim that a low-noise simulation demonstrates real SNR.
6. **Methods and inverse EEG.** Use MNE/EEGLAB and simple, independently implemented baselines. Compare noise, montage mis-registration, forward mismatch and priors; report null-space ambiguity and conditional uncertainty. Sensor fit alone is not source recovery, thought decoding or mental-health inference.
7. **Reproducible BCI task benchmarks.** Provide controlled synthetic and later permitted published-data adapters, predeclared cross-session/device splits and failure-preserving reports. Separate offline decoding from online latency, transfer and meaningful user agency.
8. **Evidence, provenance and governance.** Preserve hypothesis → protocol → data/version/rights → code → run → failures → finding → independently reviewed claim; keep permissions and human rights separate from computable scores.

**Do not build a new monolithic EEG analysis package.** Reuse mature tools through *optional* pinned adapters when they demonstrably help. Maintain one dependency-light core for validation, contracts and synthetic reproduction. Research domains can remain internal modules until external usage demonstrates a real release/governance boundary.

## Concrete open research interfaces to implement (proposed, not current features)

### Proposed `ElectrodeLayout` v0.1

Define an independent *design-target* object with `layout_id`, `revision`, `headform_id`, fiducial definitions, `coordinate_frame`, `unit`, a list of unique EEG electrode labels with local XYZ coordinates, `geometry_source_hash`, and `origin: SYNTHETIC_DESIGN_TARGET`. Distinguish **idealized** target sites from digitized, measured locations using explicit disjoint types. A failed or ambiguous transform must produce an error, never silently assume millimeters or meters.

Test: duplicate electrode names, reference/ground conflicts, impossible or missing frames, zero or negative design dimensions, wrong scale, NaNs, inconsistent orientation, nonmatching exported geometry, absence of provenance. No "fit to an arbitrary human" assertion.

### Proposed `AcquisitionManifest` v0.1

Hardware identity, version/firmware, channel-to-contact mapping, explicit reference and grounding, gain, units, nominal and *measured* sampling clocks separately, optional event-marker method, amplifier noise-test method, source authenticity, permissions and privacy classification. Synthetic boards and phantom waveforms should exercise the contract before real hardware is considered.

A validated manifest establishes **structural completeness**, not electrical safety, authentic calibration, human consent or a true neurophysiological signal.

### Proposed `ExperimentReceipt` v0.1

Protocol hash, code revision, environment/seed, input class and immutable checksums, preregistered metrics, outcome distributions, exclusions, adverse outcomes, negative controls, missing data, uncertainties and evidence ceiling. Add RO-Crate interchange without claiming certified scientific results.

Do not mix no-answer, not-measured, failed, and zero. Those states have different scientific meanings.

## Design of experiments: report the failure surfaces

Start a small **headform-only** test matrix across declared size variants, electrode locations, joint settings and mounting iterations. Test both translation and rotational perturbations on a nonhuman headform when a proper apparatus exists. Report physical measurements only when instruments and calibration/rights have been independently reviewed.

For signal tests, build an external test-signal phantom and independently characterized measurement chain under qualified review, then compare reference-vs-candidate acquisition. Prespecify signal families, frequency bands, amplitudes, intentional line interference, movement-like artifacts, clocks and failures. Never substitute a synthetic trace for measured amplifier validation.

For BCI models, isolate subjects, sessions and devices as independent evaluation units where appropriate. Prohibit train/test leakage through preprocessing or adjacent windows. Include drift, rejection/abstention, artifact-only controls, and honest worst-case reporting.

## Community design: give people a tangible first contribution

A contributor should have a clear route independent of location, institutional affiliation, expensive sensors or neuroscience training:

| Role | Starter issue | Done means |
| --- | --- | --- |
| Beginner / translator | Reproduce quickstart, improve plain-language glossary or translate one worked example | Independent install log and correct disclaimers |
| CAD designer / maker | Implement a **headform-only** concept in FreeCAD or OpenSCAD | Native editable files, units/frames, source hash, export/QC report, known limitations |
| Electronics researcher | Audit a published acquisition board's documentation and public safety limitations | Versioned reference card without unsafe wiring claims |
| EEG researcher | Add reproducible synthetic artifact/clock test with negative controls | Frozen procedure, statistical unit, failure cases and scientific scope |
| ML researcher | Add a leakage-resistant baseline against one established evaluation protocol | Exact splits, calibration, uncertainty, no outcome cherry-picking |
| Accessibility reviewer | Test setup on diverse headform geometries and devices | Structured failure reports, no demographic inference |
| Security/privacy reviewer | Threat-model staged-source indexing, exports and agent access | Negative tests for sensitive file leakage and tool overreach |
| External reviewer | Reproduce a report on a clean machine | Setup friction, fixed hashes, discrepancies and independent outcome |

**Evidence-based community incentives:** public acknowledgments, reproducible experiment cards, credited contributions, citation metadata for releases, "known limitations" badges, independent third-party reviews and repair-friendly design histories. No leaderboard based on purported thoughts decoded, injuries prevented, or scalp recordings shared.

Review scientific claims with *domain* maintainers: CAD + mechanical reviews for geometry; electrophysiology for acquisition/data analysis; privacy and human-subjects expertise for participant studies. A single green CI badge cannot replace those checks.

### Governance and safeguards from day one

- Adopt a [code of conduct](../CODE_OF_CONDUCT.md) with a private reporting route, respectful discussion expectations and documented response/appeal process before inviting large-scale community participation.
- Document maintainer ownership, versioning and breaking-change policy. Track rejected hypotheses and unsuccessful reproductions, not just positive demonstrations.
- Label issue classes `good-first-issue`, `needs-reproduction`, `hardware-review`, `science-review`, `privacy-review`, `documentation` and `unsafe-claim`; contributors should not infer labels confer approval.
- CI checks code and catalog structure; qualified reviewers check electrical/human safety, legal rights and experimental interpretation.
- Accept neither identifiable human EEG nor private MRI/head scans in public issues, source snapshots, screenshots, agent indexes or CI artifacts.
- Never train models on contributed personal recordings without separate permissions and explicit, revocable participant consent.
- Minimize dependencies on cloud services and licensing lock-in; support offline participation and accessible documentation.

## Phased roadmap with objective gates

### P0: accessible, bounded foundation (now)
- Publish this landscape, read-only catalog and negative tests; link the [evidence contract](research-contract.md).
- Give beginners a **zero-hardware** reproduction experience on Windows, macOS and Linux.
- Make contributor paths, owner map and safety expectations navigable within five minutes.
- Gate: public audit and tests pass, no unreviewed data or imported third-party code, no evidence promotion.

### P1: build one *nonfunctional* reference artifact
- Add a backend-neutral headform-only geometry specification plus an OpenSCAD/CadQuery generator.
- Add nominal montage targets with explicit geometry frames, simulated clearance and export QC.
- Optionally reproduce the same mock-up in Zoo KCL, recording tool versions, human review and dimensional comparisons.
- Gate: outside contributor can reproduce native source and exported geometry with bounded dimension differences on an independent OS. No participant fit or protective claim.

### P1: scientifically useful synthetic EEG quality lab
- Add simulated amplifier characteristics, artifacts, bad contacts, clock drift and dropped-sample scenarios with independently expressed baselines.
- Add a **synthetic** BrainFlow board adapter only when it beats a direct built-in fixture for ease of testing.
- Gate: negative tests detect intentional unit conversions, artifacts and timing failures; reproducibility receipt preserves each failed case.

### P2: controlled research interoperability
- BIDS-aligned, pinned metadata formats; optional MNE and MNE-BIDS conversion; trusted-local XERJ benchmark against lexical and `rg`.
- A UI that lets users compare assumptions, code, geometry and synthetic waveforms; agent suggestions always cite exact source/version and never execute arbitrary commands.
- Gate: independent users reproduce task and understand failure claims; retrieval improves measured answer attribution without indexing protected data.

### P3: independent scientific validation partners
- Obtain qualified reviewer sign-off for applicable nonhuman measurements, instrument calibration and rights.
- Preregister a narrow model/bench validation question; keep all adverse and contradictory outcomes.
- For any later human feasibility protocol, require separate qualified electrical/biocompatibility reviews, informed-consent/governance, security review and relevant ethics or regulatory approvals. No automatic graduation from S0.
- Gate: signed, independently verifiable study evidence for **only** the declared question and context of use.

### P4: a healthy international contributor commons
- Independent maintainers for distinct domains; multilingual learning materials; documented RFC decision process; sustainable issue triage and release channels.
- A curated gallery of **reproducible** artifact manifests and scientific methods, not unverified safety rankings.
- Gate: outside-maintainer review, repeated independent reproduction and clear scientific authority boundaries.

## Adoption metrics worth tracking

Measure **time-to-first-successful-reproduction**, contributor setup failure rate, outside-PR acceptance, repeated independent runs, documented failure coverage, reopened-regression rate, source/version citation accuracy, unresolved license blockers and number of genuinely usable public examples. Neither GitHub stars nor number of EEG channels is a validation metric.

## Current limitations

This catalog is read-only and metadata-only: its dates, documentation URLs, descriptions and license statuses are **not** continuously verified. A project link is not endorsement, approval or automatic permission to redistribute upstream resources. Zoo, XERJ, optional signal toolkits and real sensors are not required to install the current core.

**The simplest distinctive promise:** the community is welcome to build and explore radically different designs while *every result carries enough provenance, uncertainty and negative controls for someone else to challenge it*.
