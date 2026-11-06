# Optional CAD and research retrieval toolchain

**Evidence ceiling: S0.** The goal is to make NeuroShield useful to future EEG-headwear researchers without requiring any one vendor, cloud subscription, search backend or AI agent. This is a **design and integration guide**, not a declaration that these external tools were installed, benchmarked or used to generate a validated wearable.

See [EEG headwear build guide](eeg-headwear-build-guide.md), [research architecture](SCIENTIFIC_ARCHITECTURE.md), [research knowledge policy](knowledge-and-retrieval.md) and [external-corpora policy](external-corpora-and-qualification.md).

## Recommended division of labor

| Tool | Best role | Limitation / rule |
| --- | --- | --- |
| [Zoo Design Studio](https://zoo.dev/) | Optional visual and AI-assisted **parametric** modeling; save editable KCL | Zoo's geometry engine is proprietary and modeling requires an internet connection; hosted operations may cost money. Not a dependency of the Python package. |
| [KCL 3](https://zoo.dev/docs/kcl) + [Zoo CLI](https://zoo.dev/docs/developer-tools/cli/manual/zoo_kcl_export) | Version-controlled `.kcl` studies; export STEP/STL/GLB; inspect generated geometry | Pin KCL/CLI version and engine configuration; generated mesh is neither a mechanical test nor a safety report. |
| [FreeCAD](https://www.freecad.org/) | Fully open-source, desktop, editable parametric mechanical designs | Track the actual version and native project files; do not assume another CAD backend reproduces every feature. |
| [CadQuery](https://cadquery.readthedocs.io/en/latest/intro.html) or [build123d](https://build123d.readthedocs.io/) | Python-first, CAD-as-code alternative for repeatable geometry | Optional dependencies; keep output conversions and measurement conventions explicit. |
| [OpenSCAD](https://openscad.org/) | Low-barrier reproducible solid-geometry concepts; already used under `cad/` | Limited for complex ergonomic surfaces; the current project geometry is intentionally non-installable. |
| [XERJ](https://github.com/xerj-org/xerj) | Optional local-first indexing and cited retrieval of **approved sources** for agents | Not a CAD engine, scientific validator or permission system. Compare with local lexical search and `rg` before adopting. |
| [BrainFlow](https://brainflow.readthedocs.io/en/stable/index.html), [MNE](https://mne.tools/) and [LSL](https://labstreaminglayer.readthedocs.io/) | Potential future acquisition, analysis and synchronized-data tools | Not connected to NeuroShield's synthetic signals today; real human recordings need separate governance. |

This is a **compositional stack**, not a shopping list. An offline contributor can do useful work with just OpenSCAD, Python, source references and the existing synthetic tests.

## Proposed portable CAD contract

Keep the scientific design parameters **backend neutral**. Do not make Zoo API responses, a KCL parser, or a vendor SDK the source of truth for the research claims.

```text
concept specification (versioned JSON, units + frames + limitations)
        |
  +-----+----------------+----------------+
  |                      |                |
OpenSCAD              CadQuery          Zoo KCL
  |                      |                |
  +-------- optional exported STEP / STL / GLB ------+
                         |
          geometry QC report + declared provenance
                         |
          independent reviewer / headform-only mock-up
```

Suggested versioned objects and filenames for a later implementation:

```text
cad/
  concepts/
    electrode-holder/
      manifest.json             # expected schema to be defined/tested
      README.md                 # scope: mannequin/headform only
      design.scad               # one minimal reproducible backend
      optional-zoo/             # main.kcl + project settings if reviewed
      optional-python/          # CAD-as-code source if reviewed
```

**None of the above example directories/files are implemented by this document.** The only existing CAD artifact is the nonfunctional OpenSCAD mount study at `cad/concept-mount.scad`. Do not represent conceptual folder names as deliverables.

The first CAD concept should be a **standalone, nonconductive, nonfunctional electrode-position indicator for a rigid headform**. It should have visually inspectable labeled placement references, and no circuit, skin contact, load path, sports-helmet attachment or claim of wearability. A separate test should verify geometry is generated and its units are plausible; a screenshot alone is inadequate.

At minimum, an export receipt should carry: source hash; tool and engine versions; parametric inputs; declared length unit and coordinate convention; format/version; output hash; bounding box and volume (when meaningful); and explicit `UNVALIDATED_NON_INSTALLABLE_CONCEPT` status. Compare exported geometry with source dimensions and fail on unexpected unit scaling or missing components. **Finite geometry, STEP export, watertight meshes and collision-free fit never certify a human-use design.**

### Zoo-specific pilot

Zoo is attractive for fast edits, visual review and agent-generated *editable* parametric geometry. KCL 3 was released in October 2026; verify the installed version before adopting samples from KCL 2.

1. In Zoo Design Studio, create a **new, synthetic headform-only** project. Do not upload participant head scans, unpublished lab designs or proprietary/restricted geometry.
2. Model one small, nonfunctional part from declared dimensions in millimeters. Keep the `main.kcl` and project settings in a separate working directory until inspected and license-reviewed.
3. Save the exact source, versions and a visible screenshot for a human design review. Compare a reference export in a second viewer for scale and orientation.
4. If you choose the optional Zoo CLI, check `zoo kcl export --help` and then use the [documented export command](https://zoo.dev/docs/developer-tools/cli/manual/zoo_kcl_export), for example:

```bash
# Illustration only: requires separate Zoo installation/account and API access.
zoo kcl export --output-format=step main.kcl ./exported
```

5. Do not enable automatic hosted CAD execution in core CI. Zoo's modeling, rendering and MCP services require connectivity and API activity may be billed; keep tokens outside source control. Compare a local OpenSCAD/CadQuery baseline before claiming Zoo reduces design time.

**Do not accept a generative agent's geometry because it looks plausible.** Review dimensions, spatial transforms, mechanical clearances, adjustable components, privacy boundaries, failed exports and material/contact assumptions with domain specialists. Zoo does not substitute for electrical, biomechanical or protective-equipment validation.

## XERJ-specific pilot: research navigation, not a model dependency

XERJ is a Rust search engine and agent-oriented MCP server. Its strength is retrieval over mixed source code, docs and curated metadata, returning passages with provenance. It does **not** give scientific authority to an article, establish software license clearance, prove a helmet design, or solve EEG inverse problems.

NeuroShield already has a local **dependency-free baseline and safe staging contracts**. Start with those:

```bash
python -m neuroshield knowledge audit --root .
python -m neuroshield corpora audit --root .
python -m neuroshield knowledge stage --root . --out ../neuroshield-code-snapshot
python -m neuroshield knowledge bench --root . --stage ../neuroshield-code-snapshot --out ../knowledge-baseline.json
python -m neuroshield corpora bench --root . --out ../corpora-baseline.json
python -m neuroshield corpora stage --root . --out ../neuroshield-source-cards
```

Only after **manual inspection** of the staged files, and only on a local, trusted machine if its XERJ security model is understood, evaluate an optional indexer:

```bash
# Requires an independently installed XERJ; these commands are NOT run by NeuroShield.
# First read https://github.com/xerj-org/xerj/blob/main/docs/SECURITY_MODEL.md
# Configure an independently installed, authenticated local-only XERJ service
# according to the installed version. Do not launch insecure or public services.
xerj --help
# Only after reviewing staged sources and verifying service authentication / bind:
xerj autoindex ../neuroshield-code-snapshot --prefix eeg-helmet-code
xerj autoindex ../neuroshield-source-cards/neural --prefix eeg-helmet-neural
xerj search "EEG coordinate frame reference electrodes"
```

Confirm CLI syntax with the installed `xerj --help`; this guide does not assert successful XERJ execution. Place the index/database **outside** any tree being indexed, including the repository. Avoid `--insecure` when handling research materials: an unauthenticated XERJ service can expose indexed sources if networking is misconfigured. Do not index `~/`, a working tree indiscriminately, raw EEG/EMG, consent forms, private lab notes, commercially restricted standards or participant head scans.

The existing catalogs `knowledge/corpora/{biomechanics,neural,evidence}.json` are **metadata only**. A future fourth "maker resources" catalog is justified only after a schema, licenses, link checks, reproducible source versions and a distinct search/benchmark use case are reviewed. Avoid turning thousands of low-quality links into an uncurated AI knowledge base.

### Measure retrieval value before adopting it

Freeze questions *before* tuning queries. Evaluate the same pinned source snapshots with:

1. dependency-free `knowledge search` / `corpora search` and `rg`;
2. XERJ's available lexical/hybrid/semantic modes (record exact version/config);
3. a blinded human check of the returned passage's *actual relevance and correctly cited source*.

Measure top-5 source Hit@5, MRR, query latency, index duration/size, source attribution accuracy, sensitive-data leakage tests and wrong-answer rate. Include contradictory sources and queries with **no answer**. A search system that answers confidently from stale or restricted documents should fail regardless of speed. Missing binaries are **NOT TESTED**, not passes or failures. Retrieval relevance is distinct from model validation or EEG information recovery.

**Adoption rule:** XERJ remains optional even if it outperforms lexical baselines. Put any client in a separate adapter/extra; never import XERJ inside core physics, acquisition or data-governance modules. Agents should return cited candidate references for human inspection, not automatically change science claims, download datasets or actuate hardware.

## Suggested staged pull requests

| Stage | Deliverable | Acceptance |
| --- | --- | --- |
| 0 | The two maker-facing guides and landing-page navigation | No altered scientific calculations or evidence tier; links reviewed |
| 1 | A backend-neutral nonfunctional headform concept manifest + OpenSCAD example | Stable dimensions/frames, deterministic geometry/QC, negative tests and clear nonwearable label |
| 2 | Optional Zoo KCL 3 source of that same concept | Manual exported STEP scale/shape comparison; cloud off core CI; cost/versions recorded |
| 3 | Independently benchmarked XERJ retrieval pilot on **approved staged sources** | Baseline comparison, honest misses/latency/citations/privacy findings |
| 4 | New synthetic-only EEG metadata / electrode layout validation module | Workflow owner, registry updates, tests, independently reviewed anatomical conventions |
| 5 | Separate consented and reviewed acquisition feasibility proposal | Electrical safety, independent ethics/legal and security signoff; no automatic move to human trials |

These stages optimize for **understandability, portability and falsifiability**, rather than the largest model, highest electrode count or most agent integrations.
