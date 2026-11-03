# Scientific architecture: purpose, boundaries and evolution

**V1.9 research navigation; current physical evidence remains S0.** This page describes the current modular science workbench, not a certified helmet, clinical device or independently validated head-impact model.

## Three questions that must remain separate

1. **Verification:** are the declared mathematical equations and algorithms implemented consistently? Cross-solver tests, convergence checks, conservation accounting and computational replay can partially answer this question.
2. **Validation:** are those equations adequate for specified *measured physical head/neck behavior*, under a stated context of use? NeuroShield has not established that.
3. **Application and interpretation:** even a model validated for one rig and impact configuration would not automatically establish concussion protection, field performance, safety certification or clinical usefulness.

The [ASME V&V 40 framework](https://www.asme.org/codes-standards/find-codes-standards/assessing-credibility-of-computational-modeling-through-verification-and-validation-application-to-medical-devices?productKey=C08418) and [FDA physics-based modeling guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/assessing-credibility-computational-modeling-and-simulation-medical-device-submissions) emphasize model credibility proportional to the intended decision and its consequences. These are references for responsible research architecture, **not** a claim that this software satisfies regulatory requirements.

Track **two independent statuses**: software readiness and scientific evidence tier. An implementation can be mature and fully covered by CI while its physical evidence remains S0.

## Keep one installable scientific library

    Researcher / external reviewer / optional research agent
                          |
          research_map (read-only discovery)
                          |
         declared question and frozen protocol
                          |
            +-------------+-------------+
            |             |             |
       Model and V&V  Measurement QC   Neural prototyping
       models/physics  source catalog  synthetic signals
       solvers/audits  csv and frames  session/ingestion
       design sweeps   trial compare   privacy primitives
            |             |             |
            +-------------+-------------+
                          |
             evidence and provenance
       S0 claims | blockers | negative controls
                          |
              reproducible artifacts
         agent_protocol | RO-Crate | replay
                          |
                optional adapters
               neurOS / XERJ / MCP
               (never prerequisites)

The current source files remain under **src/neuroshield/**. Do not break public imports for cosmetic package moves. The new curated registry at [knowledge/research-workflows.json](../knowledge/research-workflows.json) describes logical domains, owners, tests, protocols, limitations and discoverable examples; its audit rejects orphaned public source modules.

A distributed microservice architecture or separately published subpackages are warranted only if independent users demonstrate distinct dependency, governance, maintenance or release needs. A future neural recording platform would need materially different privacy, safety and human research oversight from laboratory nonhuman biomechanics.

## Scientific object contract

Every independently interpretable experiment should eventually preserve these linked objects:

| Object | Required content | Boundary |
| --- | --- | --- |
| Question/context of use | Falsifiable prediction, alternative explanations, conditions of applicability | Never expand generality after examining results |
| Protocol | Predeclared trial unit, apparatus, timing, units, frames, methods, controls and analysis windows | Protocol hashes do not prove when a protocol was frozen |
| Dataset | Permission scope, source version, raw-file checksum, acquisition/calibration provenance | Third-party data stay local and are not automatically authenticated |
| Run | Source revision, environment, inputs, numerical outputs and failures | Reproduction of code is not validation of its physics |
| Finding | Primary and adverse outcomes, uncertainty, negative controls and discrepancies | Do not select only favorable impacts |
| Claim | Related evidence registry item, bounded interpretation and independent reviewer decision | No automatic promotion above S0 |

The code already supports several of these components for *synthetic* work, but not an end-to-end physical qualification. RO-Crate 1.3 and its third-party validator support portable metadata; they do **not** establish authorship, licensing, calibration or physical accuracy. Use [RO-Crate 1.3](https://www.researchobject.org/ro-crate/specification/1.3/index.html) and the [FAIR4RS research software principles](https://www.nature.com/articles/s41597-022-01710-x) as interoperability references, not check-box certifications.

## Repository responsibilities

| Location | Owner responsibility | Explicitly excluded |
| --- | --- | --- |
| src/neuroshield | Physics, mathematical utilities, structural intake, numerical audit, provenance and small offline interfaces | Private measurements, general agent shell authority |
| tests | Reproducible positive/negative and scientific boundary tests | Real athlete data or restrictive source bytes |
| examples | Versioned, clearly synthetic fixtures | Unapproved third-party data mislabeled synthetic |
| knowledge | S0 source and claim registry; machine-readable workflow navigation | Imported standards, patient data or clinical authority |
| docs | Stable onboarding, experiment methods, historical protocols and limits | Unsupported safety marketing |
| cad | Non-installable OpenSCAD concept geometry | Protective equipment design approval |
| .github/workflows | Platform, packaging and research-contract checks | Automatic promotion to physical validation |

Future datasets/, services/ or hardware/ trees are **not current prerequisites**. Add them only with verified demand, permissions, safety review and stable ownership.

## Highest-value experiments, ordered

**P0: qualified real data.** Finish a proper file-level Borealis rights/documentation review and independently checked head-neck instrument/coordinate conventions. Reproduce a narrowly defined *measurement* outcome on one authorized test. E-scooter crashes cannot automatically validate a football facemask simulation.

**P0: independent outside contributor.** Ask a scientist unfamiliar with the code to install a clean wheel and complete the fixed reproduction exercise. Track installation failures and independent hashes. Internal CI is not outside scientific review.

**P1: measured-versus-predicted model challenge.** Once inputs are physically applicable, freeze test setup, coefficients, validation set and uncertainty budget before viewing performance. Compare translational and rotational head outcomes and neck load when measured. Treat replicate trials as statistical units, not each sensor sample.

**P1: standards of software publication.** Add stable API/release and citation metadata after external adoption and ensure that the evidence/claim register includes each new externally interpreted method.

**P2: agent integration.** Benchmark whether optional neurOS, XERJ or MCP adapters actually improve research reproduction and review beyond the plain Python tools. Preserve offline operation and a restricted, testable authority boundary.

## Contribution rule

When changing physics, filtering, coordinate frames, data mapping or claim interpretation, update the owning workflow, write a falsifiable test with negative controls, document units and uncertainty, and preserve failure cases. A preprocessing change is not merely a visualization change. If a new module has no workflow owner, CI must fail until its scientific responsibility and limitations are explicit.

The [earlier architecture plan](architecture-and-next-experiments.md) remains an archived design record; this document is the stable current architectural entry point.
