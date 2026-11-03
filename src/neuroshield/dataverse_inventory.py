"""Offline Borealis Dataverse metadata and file-checksum intake. S0 only.

No network, raw-signal inspection, authenticity, file-license, calibration,
helmet-performance or concussion-safety approval. Provider MD5 is not a signature.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

SCHEMA = "neuroshield.dataverse-inventory/0.1"
DOI = "doi:10.5683/SP3/ZUZMCM"
TRIALS = tuple(f"Crash_{i}" for i in range(1, 7))
HEX_SIZES = {"MD5": 32, "SHA-1": 40, "SHA-256": 64, "SHA-512": 128}
MAX_JSON_BYTES = 8_000_000
MAX_FILES = 2500
SAFE_NAME = re.compile(r"[a-zA-Z0-9_.-]{1,160}\Z")


def _unique(pairs):
    result = {}
    for key, val in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key in provider response")
        result[key] = val
    return result


def _regular(path, limit=None):
    if path.is_symlink() or not path.is_file():
        raise ValueError("Expected a nonsymlink regular file")
    st = path.stat()
    if st.st_size <= 0 or (limit is not None and st.st_size > limit):
        raise ValueError("Empty or oversized file")
    return st


def _digest(path, algorithm):
    kind = {"MD5":"md5","SHA-1":"sha1","SHA-256":"sha256","SHA-512":"sha512"}[algorithm]
    digest = hashlib.new(kind, usedforsecurity=False) if kind == "md5" else hashlib.new(kind)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _snapshot(path):
    st = _regular(path, MAX_JSON_BYTES)
    raw = path.read_bytes()
    if len(raw) != st.st_size:
        raise ValueError("Metadata size changed while reading")
    try:
        doc = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique,
                         parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid UTF-8 Dataverse JSON") from exc
    if not isinstance(doc, dict) or doc.get("status") != "OK":
        raise ValueError("Expected Dataverse API OK response")
    data = doc.get("data")
    if not isinstance(data, dict) or data.get("persistentId") != DOI:
        raise ValueError("Wrong dataset DOI")
    version = data.get("latestVersion")
    if not isinstance(version, dict) or version.get("versionState") != "RELEASED":
        raise ValueError("Require released dataset version, not draft")
    if any(type(version.get(k)) is not int or not 0 <= version[k] <= 999
           for k in ("versionNumber", "versionMinorNumber")):
        raise ValueError("Dataset version must be pinned")
    entries = version.get("files")
    if not isinstance(entries, list) or not 1 <= len(entries) <= MAX_FILES:
        raise ValueError("Invalid provider file list")
    sha = hashlib.sha256(raw).hexdigest()
    if _regular(path, MAX_JSON_BYTES).st_size != len(raw) or _digest(path, "SHA-256") != sha:
        raise ValueError("Metadata changed during inspection")
    return entries, f'{version["versionNumber"]}.{version["versionMinorNumber"]}', sha


def _selected_entry(entry):
    if not isinstance(entry, dict) or type(entry.get("restricted")) is not bool:
        raise ValueError("Missing explicit provider access restriction flag")
    data = entry.get("dataFile")
    if not isinstance(data, dict):
        raise ValueError("No provider datafile object")
    label = entry.get("label")
    if not isinstance(label, str) or not SAFE_NAME.fullmatch(label) or data.get("filename") != label:
        raise ValueError("Unsafe/inconsistent file name")
    folder = entry.get("directoryLabel", "")
    if (not isinstance(folder, str) or folder.startswith("/") or "\\" in folder
        or len(folder) > 360 or any(x in (".", "..") for x in folder.split("/"))):
        raise ValueError("Unsafe provider directory label")
    fid, size = data.get("id"), data.get("filesize")
    if type(fid) is not int or fid <= 0 or type(size) is not int or size <= 0:
        raise ValueError("Invalid provider datafile id/size")
    checksum = data.get("checksum")
    if not isinstance(checksum, dict):
        raise ValueError("Selected file has no provider checksum")
    kind, value = checksum.get("type"), checksum.get("value")
    if (kind not in HEX_SIZES or not isinstance(value, str)
        or len(value) != HEX_SIZES[kind]
        or re.fullmatch(r"[0-9a-fA-F]+", value) is None):
        raise ValueError("Invalid provider checksum")
    return {"datafile_id":fid, "filename":label, "directory":folder,
            "bytes":size, "restricted":entry["restricted"],
            "provider_checksum":{"type":kind,"value":value.lower()}}


def inspect_snapshot(snapshot, *, trial="Crash_1"):
    if trial not in TRIALS:
        raise ValueError("Unsupported or unspecified trial")
    entries, version, digest = _snapshot(Path(snapshot))
    folder = f"Data_open_Repository/{trial}/Measurement_data"
    expected = {"trial_csv":(folder,f"{trial}.csv"),
                "trial_measurement_readme":(folder,"_Read_me.txt"),
                "repository_readme":("Data_open_Repository","_Read_me.txt")}
    selected, used = {}, set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Malformed provider file listing")
        label, path = entry.get("label"), entry.get("directoryLabel", "")
        if (label in (f"{trial}.csv", "_Read_me.txt") and isinstance(path, str)
            and (path.startswith("/") or "\\" in path
                 or any(x in (".", "..") for x in path.split("/")))):
            raise ValueError("Unsafe selected-trial directory")
        for role, (directory, basename) in expected.items():
            if label == basename and isinstance(path, str) and path.rstrip("/") == directory:
                if role in selected:
                    raise ValueError("Duplicate selected provider data file")
                info = _selected_entry(entry)
                if info["datafile_id"] in used:
                    raise ValueError("Duplicate provider datafile id")
                used.add(info["datafile_id"])
                selected[role] = info
    blockers = [role.upper()+"_MISSING" for role in expected if role not in selected]
    blockers += [role.upper()+"_RESTRICTED" for role,info in selected.items() if info["restricted"]]
    blockers += ["SOURCE_METADATA_NOT_AUTHENTICATED", "FILE_LEVEL_RIGHTS_REVIEW_REQUIRED",
                 "MEASUREMENT_CHANNELS_UNREVIEWED", "INSTRUMENT_CALIBRATION_UNREVIEWED"]
    return {"schema_version":SCHEMA, "status":"BLOCKED_SOURCE_REVIEW",
            "scientific_evidence_level":"S0", "dataset_doi":DOI, "dataset_version":version,
            "metadata_snapshot_sha256":digest, "trial":trial, "selected_files":selected,
            "blockers":blockers, "source_identity_verified":False,
            "file_rights_approved":False, "mapping_approved":False,
            "calibration_verified":False, "data_import_authorized":False,
            "physical_validation":False,
            "notes":"Untrusted offline metadata, not permission, measured data, calibration, or helmet validation. MD5 checksums are not signatures."}


def verify_local_file(snapshot, local_file, *, trial="Crash_1"):
    inventory = inspect_snapshot(snapshot, trial=trial)
    info = inventory["selected_files"].get("trial_csv")
    if info is None or info["restricted"]:
        raise ValueError("Public trial CSV metadata required for byte check")
    path = Path(local_file)
    before = _regular(path)
    if before.st_size != info["bytes"]:
        raise ValueError("Local file size differs from provider metadata")
    observed = _digest(path, info["provider_checksum"]["type"])
    sha = _digest(path, "SHA-256")
    after = _regular(path)
    if ((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)
        != (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)):
        raise ValueError("Local file changed during inspection")
    matched = observed == info["provider_checksum"]["value"]
    return {"schema_version":SCHEMA, "status":("CHECKSUM_MATCHES_UNAUTHENTICATED_SNAPSHOT"
              if matched else "FAILED_CHECKSUM_MISMATCH"),
            "scientific_evidence_level":"S0", "dataset_doi":DOI,
            "dataset_version":inventory["dataset_version"], "trial":trial,
            "metadata_snapshot_sha256":inventory["metadata_snapshot_sha256"],
            "file_sha256":sha, "file_bytes":before.st_size,
            "provider_checksum_algorithm":info["provider_checksum"]["type"],
            "provider_checksum_matched":matched, "source_identity_verified":False,
            "mapping_approved":False, "calibration_verified":False,
            "data_import_authorized":False, "physical_validation":False,
            "note":"Byte consistency with unauthenticated metadata is not provenance authentication, license approval or physical validation."}


def main(argv=None):
    p = argparse.ArgumentParser(description="Offline Dataverse metadata and file integrity review")
    sub = p.add_subparsers(dest="command", required=True)
    a = sub.add_parser("inspect")
    a.add_argument("snapshot",type=Path)
    b = sub.add_parser("verify-file")
    b.add_argument("snapshot",type=Path)
    b.add_argument("local_file",type=Path)
    for cmd in (a,b):
        cmd.add_argument("--trial",choices=TRIALS,default="Crash_1")
        cmd.add_argument("--out",type=Path)
    args = p.parse_args(argv)
    try:
        result = (inspect_snapshot(args.snapshot,trial=args.trial) if args.command=="inspect"
                  else verify_local_file(args.snapshot,args.local_file,trial=args.trial))
        encoded = json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n"
        if args.out is not None:
            source_paths = [args.snapshot]
            if args.command=="verify-file":
                source_paths.append(args.local_file)
            if args.out.exists() or args.out.is_symlink() or any(
                    args.out.resolve()==q.resolve() for q in source_paths):
                raise ValueError("Output must be a new file distinct from input")
            with args.out.open("x",encoding="utf-8",newline="\n") as stream:
                stream.write(encoded)
        else:
            print(encoded,end="")
    except (OSError,ValueError,TypeError,KeyError,UnicodeError) as exc:
        p.error(str(exc))
    return 2 if result["status"]=="FAILED_CHECKSUM_MISMATCH" else 0

if __name__=="__main__":
    raise SystemExit(main())
