# NeuroCap Assembly Laboratory v1: cap, ear and acquisition-envelope studies

**Evidence status: S0 synthetic only.** This is a reproducible *fictional-headform* visualization and parametric OpenSCAD concept. It is **not** a finished headphone, a wearable insert, electrode holder, skin-contact component, 10–20 montage, measured anatomical model, medical product, sports helmet accessory, or safety-qualified build. No participant scans, recordings, electrode performance or contact-pressure measurements are included.

**What works in this PR:** versioned geometry manifest, offline-capable browser assembly viewer, configurable visibility/explosion/rotation, scripted OpenSCAD geometry generation, provenance receipt, and negative tests. All seven visible layers are represented, but **none is a manufacturable or cleared human-use part**. The main NeuroShield scientific computations remain unchanged.

## Open the viewer now

From the repository root, no dependencies beyond Python 3.10 are needed:

~~~bash
cd cad/neurocap
python -m http.server 8766 --bind 127.0.0.1
~~~

Navigate to **http://127.0.0.1:8766/**. Drag to rotate; wheel to zoom; choose front/side/top; toggle part groups; use the exploded-view slider. View-site labels are symbolic. The webpage reads **manifest.json** at runtime, and does not use CDNs, an AI service, analytics, user data, or private network requests. A static file opened with \`file://\` may not allow local JSON fetch, so a loopback server is used.

## Generate the editable CAD study

From the repo root:

~~~bash
python cad/neurocap/build.py \
  --manifest cad/neurocap/manifest.json \
  --out ../neurocap-assembly-SYNTHETIC.scad \
  --receipt ../neurocap-assembly-receipt-SYNTHETIC.json

python -m unittest discover -s tests -p 'test_neurocap_assembly.py' -v
~~~

Open the generated \`.scad\` in [OpenSCAD](https://openscad.org/). Toggle \`show_*\` modules at the top. The receipt records the exact input/source hashes and unvalidated status, so a clean-machine reproduction can compare results. This is a symbolic geometric model with round markers and loops, not electrode engineering geometry. OpenSCAD \`F5\` preview is expected to be faster than high-resolution CSG rendering.

The generator and viewer share a **single versioned JSON geometry manifest** in millimeters, with an explicit right-handed coordinate frame: **+x right, +y anterior/front/brim, +z superior/top**. Ellipsoid center is origin. None of these coordinates represent measured anatomy.

## What is currently modeled?

| Group | What the current viewer shows | What is not established |
|---|---|---|
| Reference headform | Ellipsoid with three radii, axes and source version | Actual head morphology, hair, asymmetry, ear landmarks |
| Cap shell | Generic crown envelope and forward-facing brim silhouette | Size-specific 6-panel seam/cloth drape, material stiffness, sweatband |
| Inner frame | Simplified circumferential band and three over-crown ribs | Fit, real compliance, retention, assembled tolerances, contact force |
| Scalp candidate sites | Six symbolic points on ellipsoid | Verified 10–20 labels, electrodes, conductive material, skin impedance |
| Ear modules | Bilateral ellipsoidal loops and two symbolic markers | Fit to pinna/mastoid, occlusion, eyewear, acoustic sealing |
| Routing | Two abstract ear-to-band paths | Real shielded cables, creepage/clearance, strain relief, motion coupling |
| Acquisition pod | Dimensional block outside rear headform | Safe electrical circuit, battery, enclosure, heat, EMI, fixation |

**Important:** component-count != electrical-channel-count. This design deliberately leaves **EEG reference, bias/ground and acquisition configuration unspecified**. The proposed ear sites, six scalp markers, and earpiece loops do not imply a usable eight-channel system. The cap shell may be too shallow to access posterior sites; actual placement must be measured and evaluated independently.

## Full part-development roadmap

### P0. Nonfunctional spatial kit: implemented visual placeholders

- \`A0-HEADFORM\`: generic mm-scale ellipsoid and axis convention; already visualized.
- \`A1-GARMENT\`: bounding cap envelope, brim and orientation; already visualized.
- \`A2-FRAME\`: band and crossed/longitudinal ribs; visualized but no snap mechanisms.
- \`A3-SCALP\`: abstract sites on reference surface; no conductive contact geometry.
- \`A4-EAR-L/R\`: detached bilateral ear supports; no anatomical placement assertion.
- \`A5-ROUTE\`: abstract line corridors for later cable pathways.
- \`A6-POD\`: free-standing dummy block to reason about electronics bulk and mass distribution.

Each visual part has a stable ID, owner/role, evidence ceiling and explicitly missing measurements.

### P1. Headform engineering studies: NOT implemented

1. **Fit geometry/reference family:** anthropometric reference headforms in multiple sizes, landmark definition, cap profile measurement method, hair clearance and textile envelope variation. Preserve source permissions and *do not upload personal scans*.
2. **Contact-cartridge interfaces:** separately adjustable, *nonconductive, nonfunctional* facsimiles for flat frontal sites and hair-bearing positions. Examine tolerance stackups, insert/remove reach and mock cleaning path. No unreviewed DIY electrode spikes or skin contact.
3. **Ear placement study:** several abstract loop, hook and soft circumaural-carrier geometries. Account for glasses, jaw movement, earpiece/headphone interference and bilateral asymmetry. Ear markers are not yet physiological contacts.
4. **Motion/strain relief:** standalone cable clips and flexible routing paths with no contact to skin, bench bending tests and movement artifact proxies.
5. **Removable pod mock-up:** separate external mounting alternatives for a *nonfunctional mass dummy*, never rigid inserts pressed between the head and certified protective equipment.
6. **Contact/assembly jig:** headform-only repeatability markers, deflection and point-load measurement jig under qualified supervision.
7. **Export governance:** reproducible STEP/mesh measurements, model-to-manifest bounding boxes, interference checks and CAD source licensing.

### P2. Independent instrumentation and safety: NOT implemented

- Qualified analogue frontend design review, component/protection audit and bench characterization (shorted inputs, electrical phantoms, crosstalk, frequency response, gain and calibration).
- NeuroDAQ ADS1299 and source license compatibility assessment **before any source/design copying**. Its publicly documented electrical interfaces and 3D frame are research references, not an automatically safe drop-in.
- Evaluate alternative electrode assemblies against an approved commercial EEG reference using a documented protocol, independent fits and honest signal quality masking **only after the necessary human/electrical reviews**.
- Separate wear duration, skin irritation, contact pressure, acoustic sealing, heat, battery behavior and charging hazard assessments. A competent qualified engineer must sign off relevant electrical safety before any person is connected to experimental electronics.
- For sports use, an entirely distinct certified-protective-equipment evaluation is required. **Never install a rigid prototype under or on a bicycle/ski helmet or alter its retention/shell/liner.**

### P3. Scientific utility: NOT implemented

Acquire properly qualified and permissioned recordings in local private storage. For each channel preserve measured montage and reference, amplifier/firmware, clock-domain, quality and uncertainty. Evaluate stationarity, speech, blink, jaw movement and movement modes against a commercial reference. Compare *useful quality-accepted neural minutes* per unit fitting time, not merely nominal channels. Then align real gameplay/controlled experiments with independently measured timing uncertainty and distinguish task signals from input/motion artifacts.

## System-level architecture

~~~text
                     VERSIONED S0 GEOMETRY
                        manifest.json
                          /       \
             HTML projection     build.py -> OpenSCAD + hash receipt
                          \       /
                   anatomy / fit review
                             |
                 P1 headform-only mockups
                             |
                  qualified safety gates
                             |
    bench electrical/phantom ---- independent human sensor feasibility
                             |
                   private multimodal sessions
                             |
             QC + event timing + behavioral modeling
~~~

This deliberately reuses the [existing EEG headwear builder guide](eeg-headwear-build-guide.md), [scientific contract](research-contract.md), [open-hardware NeuroDAQ reuse plan in draft PR #41](https://github.com/sidhulyalkar/eeg-helmet/pull/41), [first headform marker lab in draft PR #38](https://github.com/sidhulyalkar/eeg-helmet/pull/38), and the [gameplay observatory draft PR #40](https://github.com/sidhulyalkar/eeg-helmet/pull/40). Keep each proposal separate until reviewed and avoid accidentally declaring an unmerged prerequisite as existing functionality on \`main\`.

## QA checklist and engineering gates

**Automated in this PR (S0 only):**
- Reject unknown units, evidence tier, origin or coordinate frame.
- Reject nonfinite dimensions, out-of-bounds radii, invalid crown rib spans and unsupported ear offsets.
- Reject duplicate scalp markers, ear-side ambiguity and assertions of measured electrodes.
- Produce byte-identical OpenSCAD and source receipts for identical fixture input.
- Reject changed skin-connection declarations or falsely qualified components.
- Confirm the visualizer has no third-party runtime, required paid API or CDN.

**Not yet tested (mandatory before physical interpretation):**
- OpenSCAD rendering on CI, self-intersections, geometric watertightness, STEP export, tolerance feasibility and independently measured headform geometry.
- Physical component deformation or force, electrode coupling, electrochemical safety, power, skin materials, EMC, user comfort or human signal validity.
- Full-browser screenshot and pointer interaction tests; manually verify in an actual browser.
- Actual EEG data, acquisition, timing or device SDK.

Document failures rather than rewriting acceptance criteria to make the concept appear complete.

## Suggested next scoped PRs

- **CAD V2:** establish a measured *generic/mannequin-only* reference family, robust static screenshot/mesh-export jobs, geometry QC for clearance and component collisions, preview snapshots.
- **CAD V3:** headform-only modular contact-cartridge geometry with reversible indexers, strain-relief mock-ups and printable *noncontact* test coupons.
- **Electrical V1:** bench-only NeuroDAQ test-signal ingestion with packet-error adversarial tests and explicit isolation/safety risk register.
- **Research UI V1:** an evidence-aware montage comparison view with distinct nominal/observed statuses and a separate safety approval workflow, no misleading heatmaps or false cognitive scores.
- **Measurement V1:** reviewed reference EEG and instrumented headform experiment design, with preregistered failure criteria and no human-data publication.

## References and license note

All CAD in this directory was independently authored as generic mathematical geometry. **No OpenBCI or NeuroDAQ CAD mesh has been imported or sublicensed.** Source code remains under this repo's Apache-2.0 license; review each third-party project's hardware/circuit/mesh license before future copying. References: [OpenBCI Ultracortex](https://github.com/OpenBCI/Ultracortex), [NeuroDAQ](https://github.com/carlos-lorenzo/neurodaq), [NeuroDAQ hardware](https://github.com/carlos-lorenzo/neurodaq-hardware), [EEG-BIDS](https://bids-specification.readthedocs.io/en/stable/modality-specific-files/electroencephalography.html), [MNE montage API](https://mne.tools/stable/generated/mne.channels.make_standard_montage.html).
