# V1.6: local nonhuman CSV structure probe

**Evidence ceiling S0.** The probe scans a user-held CSV with an **explicit nonhuman or synthetic origin declaration**. It does not fetch Borealis files, detect concussion, determine equipment compliance, approve source licenses, map sensor axes automatically, or produce physical validation. A declaration is not independent proof of nonhuman origin.

## Why a generic probe

The publicly indexed [Borealis dataset](https://doi.org/10.5683/SP3/ZUZMCM) (Bailly et al., 2024, DOI 10.5683/SP3/ZUZMCM) advertises six e-scooter curb-crash tests with a Hybrid III anthropomorphic test device, head acceleration, and upper-neck force/moment recordings. Its repository lists a `Crash_1.csv` file of approximately 31.4 MB and a measurement-specific readme. The dataset landing page lists CC BY 4.0. **We have not verified the CSV's actual channel names, row structure, unit conversions, frame orientation, calibration certificates, or file-level reuse terms.** We therefore do not hard-code a Borealis-specific parser or copy any third-party measurements into Git.

## Synthetic smoke check

Run on an included synthetic fixture:

```bash
python -m neuroshield.csv_probe examples/headform-SYNTHETIC.csv \
  --source-id synthetic-headform-local \
  --origin SYNTHETIC_HEADFORM_FIXTURE \
  --time-column 0 --time-unit s \
  --out ../synthetic-csv-probe.json
```

If you have independently checked that a **local** Borealis file is nonhuman and its terms permit your intended examination, keep it outside this repository and start with **unmapped** inspection:

```bash
python -m neuroshield.csv_probe /your/local/path/Crash_1.csv \
  --source-id borealis-escooter-headneck-2024 \
  --origin NONHUMAN_INSTRUMENTED_HEADFORM \
  --out ../borealis-file-structure.json
```

This command exports only file SHA-256, size, number of rows and columns, per-column **hashed headers**, numeric-like fractions in the first 128 rows and explicit scientific blockers. It exports **no actual signal values and no raw filename or local path**.

For a **manually approved** time channel, rerun with `--time-column N --time-unit ms` (or `s`/`us`). It detects nonmonotonic/nonfinite timestamps, large gaps and interval jitter, but performs **no resampling**. Units cannot be guessed from filenames or column titles. To inspect labels **locally at your own discretion**, opt in with `--include-header-labels` and do not share the resulting report without reviewing it.

The probe accepts UTF-8 CSV with comma, semicolon, or tab delimiters (explicit `--delimiter`); maximum 64,000,000 bytes, 750,000 rows, 256 columns. Other layouts, encodings, multirow headers and binary acquisition formats need a separately reviewed parser. Do not silently strip invalid rows to make a dataset pass. It refuses symlink input, inconsistent row lengths, duplicate headers and existing output paths.

## Readiness gates for a genuine measured trial

1. **Permission and provenance:** actual file-level rights, dataset version, checksum and correct citation.
2. **Instrument declaration:** exact channel names, SI conversion factors, orientation, sensor location, gravity handling, filtering, sampling clock and saturation limits.
3. **Independent calibration:** documented calibration chain and measurement uncertainty, reviewed by a qualified laboratory.
4. **Protocol matching:** impact configuration and holdout logic, no pooling across unlike crashes.
5. **Model challenge:** preregister a narrow forward-prediction test only after the first four gates. The current three-body toy solver has not been calibrated to this dataset.

A successful structure probe is a **file-inspection receipt, not an approved data importer**. Its report always retains `data_import_authorized: false`, `calibration_verified: false`, `mapping_approved: false` and `scientific_evidence_level: S0`.

For broader source readiness review, use `python -m neuroshield.source_intake --root .`. See Issue #11.
