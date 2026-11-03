# V1.8: Borealis Dataverse metadata and byte-consistency intake

**Research evidence ceiling: S0.** This is an offline parser of a *saved, unauthenticated* provider API response. It never downloads raw data, contacts the provider, interprets head/neck channels, approves data rights, authenticates source files, or validates concussion protection.

## Why metadata first?

The [Borealis dataset](https://doi.org/10.5683/SP3/ZUZMCM) by Bailly et al. (2024) is a candidate for evaluating *data processing* on nonhuman Hybrid III e-scooter crash recordings. Its public catalog lists a `Crash_1.csv` of approximately 31.4 MB, a measurement-specific `_Read_me.txt` and a repository-level `_Read_me.txt`. Its landing page declares CC BY 4.0. We have **not** independently inspected these files, their per-file usage conditions, physical coordinate definitions, filters or instrument calibration. These are not football-facemask impacts.

Dataverse's official [Native API documentation](https://guides.dataverse.org/en/latest/api/native-api.html) describes dataset `latestVersion.files[]` metadata, per-file access restrictions, provider file IDs, sizes and checksums. The [Data Access API](https://guides.dataverse.org/en/latest/api/dataaccess.html) is separate. This code does **not** call either one.

## 1. Save a provider metadata response

A researcher with authorized access may save *public metadata only* outside the repository. This example follows the documented API shape, but **has not been confirmed to work against Borealis from this execution environment**:

```sh
curl --fail --show-error --location \
  'https://borealisdata.ca/api/datasets/:persistentId/?persistentId=doi%3A10.5683%2FSP3%2FZUZMCM' \
  --output ../borealis-dataverse-metadata.json
```

Do not place API credentials in files or URLs. Do not circumvent authorization or access restrictions. The tool refuses incorrect DOIs, unpublished/draft versions, missing version numbers, oversized metadata, malformed or duplicate JSON keys and ambiguous file identities.

## 2. Review the exact files

```sh
python -m neuroshield.dataverse_inventory inspect \
  ../borealis-dataverse-metadata.json \
  --trial Crash_1 --out ../crash1-inventory.json
```

This reports the source-snapshot SHA-256, declared released dataset version, and the **three selected** file metadata objects: trial CSV, measurement README and repository README. Each record includes provider file ID, size, checksum algorithm/digest and restricted flag. A missing or restricted file is explicitly blocked. The rest of the dataset is not copied or enumerated. All reports say `BLOCKED_SOURCE_REVIEW`, `S0` and `data_import_authorized=false`.

## 3. Compare a locally obtained original file with provider metadata

After independently verifying the actual terms for the file and obtaining it through an authorized mechanism **outside Git**, you may perform only a byte-consistency check:

```sh
python -m neuroshield.dataverse_inventory verify-file \
  ../borealis-dataverse-metadata.json \
  /your/local/authorized/Crash_1.csv \
  --trial Crash_1 --out ../crash1-consistency.json
```

The command compares file size and a streamed provider-listed MD5/SHA checksum, and separately records local SHA-256. It **does not read CSV values as measurements or export samples**. A mismatch gets `FAILED_CHECKSUM_MISMATCH` and a nonzero CLI exit code. A match gets `CHECKSUM_MATCHES_UNAUTHENTICATED_SNAPSHOT`, **not** verified origin, calibration, permission or model validity. The snapshot could itself be forged. MD5 is not collision-resistant or a signature.

If Dataverse transforms a tabular download, the downloaded bytes may differ from the original provider-listed checksum. Compare the **original** file rather than treating a transformed export's mismatch as evidence corruption.

## 4. Physical evidence remains blocked

The next task is to read the actual `_Read_me.txt` and calibration notes, verify axes, time origins, filtering, units, head and neck reference points and uncertainties, then use `neuroshield.csv_probe` and the V1.7 `measurement_mapping` *review-only* tools. Do not fabricate a channel map or manually reassign a neck moment to another point without the signed wrench transformation.

One crash file is not a football helmet test; different configurations are not independent repetitions. A matching provider digest is not an externally verified lab report. No part of this workflow raises evidence above S0 or claims reduced concussion risk. Track the physical-data qualifications in Issue #11.
