# External nonhuman biomechanics evidence gate (V0.8)

The `neuroshield.external_evidence` module performs **metadata-only**, offline qualification review. It is not a physical-model validation engine, calibration certificate verifier, medical device, or license authority.

```bash
python -m neuroshield.external_evidence evidence-record.json --out review-report.json
```

Input record keys: `schema_version` (must be `neuroshield.external-evidence/0.1`), `dataset_id`, `origin`, `source`, `rights`, `acquisition`, and `evaluation`. Source records must include URL, SHA-256, license document and citation. Rights are declarative approvals for local analysis and redistribution; acquisition declarations describe calibration, coordinate-frame and uncertainty review; evaluation specifies preregistered metrics, replicates and independent lab review.

The process exits with code 2 if **BLOCKED**, and code 0 if **REVIEW_REQUIRED**, meaning only that metadata declarations passed software checks. Even if every field is attested, evidence stays **S0**, requiring independent verification of the actual source, license, instrument calibration and laboratory methods. Synthetic fixtures cannot become physical evidence.

Never commit third-party raw headform files or human recordings. No claim of reduced concussion risk, NOCSAE certification, or protective performance is supported by this gate. See issue #11 for the external research plan.
