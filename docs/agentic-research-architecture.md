# Agent-ready research architecture: scientific kernels first

**Status:** This is an architectural proposal with one implemented S0, synthetic-only integration slice. No medical, protective-hardware, real-data or institutional authorization is implied.

## Mission and target users

NeuroShield should help an independent researcher, student or laboratory **formulate, falsify and reproduce narrowly stated claims** about head/neck mechanics and measurement methods. It is not a helmet-ranking system, a concussion predictor or a general-purpose autonomous science agent.

Key users and jobs:

1. **Biomechanics researchers:** reproduce numerical assumptions, check headform coordinate frames, import a permitted external test locally, quantify disagreement and investigate failure modes.
2. **EEG/EMG researchers:** document timing, artifacts, electrode/contact quality and eventual consent-backed feasibility independently from mechanical injury claims.
3. **Hardware engineers and makers:** explore *non-installable* concepts and export fabrication-adjacent diagrams **without** mistaking a prototype for certified protective equipment.
4. **Research agents and reviewers:** search source/evidence, propose controlled hypotheses and schedule *allowlisted* software experiments; obtain evidence-linked reports for human review.

## Boundaries and layers

```text
Research questions / human reviewers / external AI agents
                 |
      TASK CONTRACT + POLICY GATE
   (fixed schema, no arbitrary commands)
                 |
     REPRODUCIBLE SCIENTIFIC KERNELS
    numerical physics | signal processing
     geometry | measurement QC | metrics
                 |
      PROVENANCE + EVIDENCE REGISTRY
    task hashes | code hashes | blockers
     numerical status != physical status
                 |
     CONTROLLED ARTIFACT INTERCHANGE
      JSON + metadata RO-Crate 1.3
                 |
        OPTIONAL EXTERNAL ADAPTERS
    XERJ | MCP server | workflow scheduler
       neurOS | other research projects
```

**Keep independent modules** as pure functions. Network-capable services and agent servers are optional wrappers. An LLM may *propose* a study; deterministic code must validate its structure and authority. Human/lab review controls any external acquisition, disclosure, hardware alteration and evidence-tier change. Never let retrieved PDFs or third-party MCP tool descriptions override code contracts.

## Implemented first slice: offline agent task protocol

`src/neuroshield/agent_protocol.py` offers two **exactly specified** operations:

- `simulate_synthetic`: fixed bounded parameters and one synthetic scenario, with full-precision peak response, physics/trace hashes, and explicitly nonphysical status.
- `audit_synthetic_numerics`: run the existing separate-integrator toy-model check and expose numerical acceptance/failure, worst-case error and source fingerprints. Numerical pass **never** upgrades S0.

The machine-readable request schema ships in the installed Python package. It explicitly forbids unknown operations, external-data origins, output-control fields, executable code, URLs and subjective safety verdicts.

```bash
python -m neuroshield.agent_protocol capabilities
python -m neuroshield.agent_protocol schema
python -m neuroshield.agent_protocol validate examples/agent-task-SYNTHETIC.json
python -m neuroshield.agent_protocol run examples/agent-task-SYNTHETIC.json --out ../agent-run-demo
python -m neuroshield.agent_protocol verify ../agent-run-demo
```

A run emits four files under a **new**, explicit output directory: `task.json`, `result.json`, `checksums.json`, `ro-crate-metadata.json`. Metadata uses a minimal RO-Crate 1.3 JSON-LD graph containing the generated report, task, checksums and software/action relationship. This was **not** independently conformance-validated against the full RO-Crate profile. SHA-256 offers a local integrity check, **not** authenticity, signatures, permission verification, or science qualification. No timestamp, host identifier, access token or user records appear in the default result; the two source-code identities and original plan fingerprint are retained.

This is **not a sandbox or production service**. An external tool host must put process isolation, filesystem authorization, resource/time quotas, authenticated requests, consent and logging around it. Never directly expose its CLI on a network.

## Research objects and graph edges (future schema)

Design a shared, typed vocabulary with traceable references:

- **Question** asks a measurable hypothesis, including an explicit null and competing mechanisms.
- **Protocol** declares apparatus, units/frames, controls, fixed analysis window, primary/secondary outcomes and stop criteria.
- **Dataset** has license, origin, retention boundary and immutable content identity; raw restricted measurements remain local.
- **Run** binds protocol + dataset/source IDs + code revision + environment + parameters + outputs.
- **Finding** records effect direction, uncertainty, negative results and failure cases.
- **Claim** links findings and reviewer decisions to an evidence tier; no automated upward promotion.

RDF/JSON-LD can later express PROV-O-style `Entity`, `Activity`, `Agent`, and the edges that connect them. Use RO-Crate for portable bundles, not a custom global graph database as a prerequisite. See W3C PROV-O and RO-Crate 1.3.

## Data classification (proposed policy)

| Class | Example | Automated execution |
|---|---|---|
| SYNTHETIC_ONLY | generated simulator output | Fixed safe operations may run locally |
| PUBLIC_METADATA | DOI, citation, license pointer | Read-only retrieval with source review |
| LICENSED_NONHUMAN | headform measurement | Local permitted use, documented reviewer and calibration checks |
| HUMAN_RESTRICTED | EEG/EMG from athletes | Outside this agent contract; separate, consented and governed platform |
| HARDWARE_ACTUATION | changing a protective helmet or impact rig | Never from unreviewed agent task |

## Agent interactions that would be useful (future; not yet implemented)

- `list_capabilities` → show schemas, evidence ceilings, unit requirements and side effects.
- `inspect_assumptions` → retrieve *pinned* code/source references and uncertainty blockers.
- `propose_experiment` → draft a preregistration to be reviewed, not silently executed.
- `run_synthetic_benchmark` → invoke only audited read-only kernels and return a reproducible crate.
- `compare_candidate` → paired headform analysis **only** after data permissions, acquisition QC and qualified oversight.
- `request_evidence_review` → route to named human reviewers and retain a signed decision record.

Prefer a narrow future MCP adapter that delegates to this package and discloses exact read/write effects. XERJ remains optional retrieval, never a grant of scientific authority. neurOS should receive explicitly labelled, consented neural records through a **separate** versioned adapter, not simulated 'brain response' as ground truth.

## Product and contribution prioritization

| Phase | Proof needed | Observable measure |
|---|---|---|
| 1. Reproducible synthetic science | independent machine repeats pinned task and gets same fingerprints | cross-platform reproducibility; negative tests |
| 2. Outside-scientist usability | external contributor can reproduce report from README within 30 minutes | completion rate, setup pain points, first independent PR |
| 3. Reputable external measurements | one licensed, calibrated nonhuman test produces documented model-versus-data error | source/calibration traceability, worst-case failure disclosure |
| 4. Experiment OS | agent-assisted hypothesis → preregistration → simulation → human decision record | fraction of auditable runs, reviewer overrides, false scientific claims |
| 5. Platform and deployment | validated modules useful beyond football in distinct sports and labs | repeat use by labs, stable public interfaces, real comparative validations |

**Counterfactual:** If XERJ, vector databases, Kubernetes or multi-agent orchestration do not improve reproduction, evidence discovery or test throughput over a plain Python package, don't adopt them. Simplicity is a feature until independently disproved.

## Scientific and operational acceptance gates

- **No safety score** from the toy model; a negative or conflicting result is a first-class output.
- **No arbitrary tool execution** from an agent, and no training or indexing on private human or proprietary input by default.
- **No permission by assertion:** a provided file or permission label is still subject to legal and scientific review.
- **No automated evidence promotion:** S1–S4 require independent human/qualified review and explicit external artifacts.
- **No silent posthoc tuning:** preregistration and holdout logic must be pinned before external measurements are compared.

## Standards path

- RO-Crate 1.3: https://www.researchobject.org/ro-crate/specification/1.3/index.html
- W3C PROV-O: https://www.w3.org/TR/prov-o/
- FAIR guidelines: https://www.gofair.foundation/fair-principles

These standards guide future interoperability; the present bundle is a minimal shape, not certified compliance or signed provenance.
