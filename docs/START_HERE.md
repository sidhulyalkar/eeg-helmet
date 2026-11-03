# Start here: NeuroShield research workbench

NeuroShield is an **open, nonclinical S0 research prototype**, not a tested protective helmet, concussion detector, certified facemask, or validated biomechanics model. It contains synthetic simulation, numerical audits, nonhuman measurement-format review tools, and reproducible research artifacts. **No measured protective benefit has been established.**

## Your first ten minutes

Use Python 3.10+ from the root of this repository:

    python -m pip install -e .
    python -m neuroshield.research_map audit --root .
    python -m neuroshield.research_map list --root .
    python -m neuroshield.agent_protocol capabilities

Then reproduce one numerical experiment without any external datasets:

    python -m neuroshield qualify-independent --scenario all --out ../numerical-audit.json

The numerical audit checks mathematical consistency **within a synthetic model**. Passing it never establishes physical predictive accuracy or protective performance.

## Choose a research question

| I want to... | Research-map identifier | Evidence boundary |
| --- | --- | --- |
| Investigate synthetic head/facemask mechanics | impact-model | Toy mechanics only |
| Audit numerical integration | numerical-verification | Solver consistency, not real-world validity |
| Find a documented nonhuman dataset | external-source-discovery | Metadata and file rights require review |
| Inspect sensor channels and coordinate frames | nonhuman-measurement-contracts | Calibration and mapping unverified |
| Examine paired trial motion trade-offs | bench-waveform-screen | Descriptive S0 comparisons, never safety rankings |
| Prototype EEG/EMG data interfaces | synthetic-neural-events | Synthetic physiology, no human recordings |
| Reproduce a bounded computation | agent-reproduction | Computational replay, not physical evidence |
| Inspect the visual demo and CAD concept | visualization-and-cad | Non-installable concepts only |

Explore the complete owner, test and protocol link for any area, for example:

    python -m neuroshield.research_map show nonhuman-measurement-contracts

Each map entry names the owning code, linked regression tests, relevant protocol, related S0 claims, a copyable example command and an explicit **not established** statement. The map is read-only: it **never executes** a suggested command, downloads data, authorizes an instrument or changes the scientific evidence level.

## Select the correct experimental design

A truly matched comparison uses the V1.10 [matched-block preflight](study-design-preflight-v1.10.md). An unpaired/factorial experiment uses the V1.11 [factorial preflight](unpaired-factorial-preflight-v1.11.md). Neither automatically performs statistical inference, and both require independently reviewed measurement provenance before physical conclusions. **Do not convert one design into another to make a tool accept it.**

## Audit the toy model before fitting it

Run `python -m neuroshield.model_diagnostics --scenario all --preset default` and read the [observable/identifiability guidance](model-sensitivity-and-observables-v1.12.md). This reveals **local synthetic sensitivity**, not physical identifiability, calibrated neck loads, 3D head kinematics or safety.

## A scientific contribution in six steps

1. Read the [scientific architecture](SCIENTIFIC_ARCHITECTURE.md) and [evidence contract](research-contract.md).
2. Pick one falsifiable hypothesis. Record the **context of use**, assumptions, alternatives, units, coordinate frames, uncertainty and conditions that would disprove it.
3. Preregister data versions, calibration, input rights, primary metrics, holdouts, time windows and negative controls **before** looking at the evaluation outcome.
4. Run the linked module tests, full unittest suite and workflow-map audit.
5. Publish **all** comparable results and failures. Do not tune clock alignment or thresholds after seeing the desired effect without transparently declaring a new exploratory analysis.
6. For an outside-scientist reproduction challenge, follow the [V1.4 exercise](reproduction-challenge-v1.4.md) and report failed setup attempts as carefully as successes.

Real nonhuman test data must remain local until proper rights, source identity, calibration and disclosure review are complete. No identifiable athlete files, private measurements, keys, or sensitive acquisition data belong in this repository or its optional research-agent index.

## Contributing and AI agents

Read [CONTRIBUTING.md](../CONTRIBUTING.md) and [AGENTS.md](../AGENTS.md). AI agents may inspect the map and propose experiments. The separate agent protocol permits only fixed, synthetic computational operations, not general shell access, protected data import, evidence-tier changes, or protective helmet modification.

If the workflow-map audit fails, repair the stale code/test/protocol/claim link instead of disabling the check. New services, orchestration layers and dependencies are justified by improved independent reproducibility or empirically demonstrated research usefulness, not by architectural fashion.
