"""Offline research-agent task contract for S0-only NeuroShield computations.

The action registry is a *fixed* allowlist, not an MCP server, autonomous agent,
security sandbox, authorization service or permission to use any physical hardware.
No network, subprocess or user-provided program is executed. Outputs are synthetic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date, datetime, timezone
from importlib.resources import files
from pathlib import Path

from . import __version__
from .models import Parameters, SCENARIOS
from .provenance import canonical_hash

SCHEMA = "neuroshield.agent-task/0.1"
RESULT_SCHEMA = "neuroshield.agent-result/0.1"
MAX_REQUEST_BYTES = 16_384
MAX_REPORT_BYTES = 2_000_000
_OPERATIONS = {
    "simulate_synthetic": {
        "description": "Summarize a deterministic illustrative synthetic impact run",
        "inputs": {"scenario": "one of facemask, oblique, lateral, rear", "parameters": "bounded mechanical parameter object, may be empty"},
        "writes": False,
        "network": False,
        "accepted_data_class": "SYNTHETIC_ONLY",
        "evidence_ceiling": "S0",
    },
    "audit_synthetic_numerics": {
        "description": "Cross-check the same toy equations with a second numerical integrator",
        "inputs": {"scenario": "one of all, facemask, oblique, lateral, rear"},
        "writes": False,
        "network": False,
        "accepted_data_class": "SYNTHETIC_ONLY",
        "evidence_ceiling": "S0",
    },
}


def capabilities() -> dict:
    """Agent-discoverable static capabilities; never a promise of physical validity."""
    return {
        "schema_version": SCHEMA,
        "protocol": "offline-json-cli",
        "request_schema": "neuroshield/schemas/agent-task.schema.json",
        "capabilities": _OPERATIONS,
        "rejected_data": ["HUMAN_RECORDING", "NONHUMAN_MEASURED", "UNKNOWN"],
        "limitations": [
            "Read-only computational actions; the CLI only writes user-approved output bundles",
            "No arbitrary code, URLs, external input files, device I/O or network access",
            "No autonomous scientific claim promotion; all outputs remain S0",
            "No evidence of head injury prevention or certified protective performance",
        ],
    }


def validate_request(request: object) -> dict:
    """Reject unknown keys, origins, scenarios, parameters and authority escalation."""
    fields = {"schema_version", "task_id", "operation", "data_class", "inputs"}
    if not isinstance(request, dict) or set(request) != fields:
        raise ValueError("Task must have exactly the five documented fields")
    if request["schema_version"] != SCHEMA:
        raise ValueError("Unsupported agent task schema")
    task_id = request["task_id"]
    if not isinstance(task_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", task_id):
        raise ValueError("Invalid task identifier")
    if request["data_class"] != "SYNTHETIC_ONLY":
        raise ValueError("Only entirely synthetic tasks are accepted")
    op = request["operation"]
    if not isinstance(op, str) or op not in _OPERATIONS:
        raise ValueError("Unknown or unauthorized operation")
    inputs = request["inputs"]
    if not isinstance(inputs, dict):
        raise ValueError("Inputs must be an object")
    if op == "simulate_synthetic":
        if set(inputs) != {"scenario", "parameters"}:
            raise ValueError("Simulation requires scenario and parameters only")
        params = Parameters.from_payload(inputs["parameters"])
        if inputs["scenario"] not in SCENARIOS:
            raise ValueError("Unknown impact scenario")
        # Replace optional parameter subsets with a single explicit representation.
        normalized = {"scenario": inputs["scenario"], "parameters": params.to_dict()}
    else:
        if set(inputs) != {"scenario"} or inputs["scenario"] not in (*SCENARIOS, "all"):
            raise ValueError("Numerical audit requires a known scenario")
        normalized = {"scenario": inputs["scenario"]}
    return {"schema_version": SCHEMA, "task_id": task_id, "operation": op,
            "data_class": "SYNTHETIC_ONLY", "inputs": normalized}


def _source_identity(operation: str) -> dict:
    """Hash exact implementation sources, normalized for checkout line endings."""
    source_names = ["models.py", "physics.py", "provenance.py", "agent_protocol.py"]
    if operation == "audit_synthetic_numerics":
        source_names += ["independent_solver.py", "independent_qualification.py"]
    return {name: hashlib.sha256(files("neuroshield").joinpath(name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            for name in source_names}


def execute(request: object) -> dict:
    """Execute an allowlisted synthetic computation in-process, without side effects."""
    task = validate_request(request)
    op = task["operation"]
    if op == "simulate_synthetic":
        from .physics import simulate
        inputs = task["inputs"]
        run = simulate(inputs["scenario"], Parameters.from_payload(inputs["parameters"]))
        payload = {"scenario": inputs["scenario"], "metrics_unrounded": run["metrics_unrounded"],
                   "mount_limit_engaged": run["metrics"]["mount_limit_engaged"],
                   "physics_scientific_fingerprint": run["provenance"]["scientific_fingerprint"],
                   "trace_sha256": run["provenance"]["execution_trace_sha256"]}
        verdict = "SYNTHETIC_DEMONSTRATION_ONLY"
    else:
        from .independent_qualification import qualify_independent
        audit = qualify_independent(task["inputs"]["scenario"])
        payload = {"scenario": task["inputs"]["scenario"],
                   "numerical_status": audit["status"], "cases_passed": audit["passed"],
                   "cases_total": audit["case_count"], "numerical_audit_sha256": audit["report_sha256"],
                   "maximum_cross_solver_fraction": max(c["worst_cross_solver_fraction"] for c in audit["cases"]),
                   "maximum_refinement_fraction": max(c["worst_reference_refinement_fraction"] for c in audit["cases"]),
                   "maximum_energy_balance_fraction": max(c["energy_balance_fraction"] for c in audit["cases"]),
                   "failed_cases": [{"scenario": c["scenario"], "design": c["design"],
                                     "reasons": c["failure_reasons"]} for c in audit["cases"]
                                     if c["status"] != "PASS_NUMERICAL_ONLY"]}
        verdict = "NUMERICAL_CHECK_ONLY" if audit["status"] == "PASS_NUMERICAL_ONLY" else "NUMERICAL_CHECK_FAILED"
    result = {"schema_version": RESULT_SCHEMA, "task_sha256": canonical_hash(task),
              "task_id": task["task_id"], "operation": op, "source_sha256": _source_identity(op),
              "data_class": "SYNTHETIC_ONLY", "scientific_evidence_level": "S0",
              "status": verdict, "result": payload,
              "limitations": ["Shared unvalidated mechanics; no physical calibration",
                              "Not helmet certification, an injury predictor or protective-performance evidence"]}
    result["result_sha256"] = canonical_hash(result)
    return result


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def _bounded_json(path: Path, limit: int) -> object:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > limit:
        raise ValueError("Missing, symlinked or oversized JSON document")
    try:
        def unique_pairs(pairs):
            obj = {}
            for key, value in pairs:
                if key in obj:
                    raise ValueError("Duplicate JSON keys are forbidden")
                obj[key] = value
            return obj
        return json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda x: (_ for _ in ()).throw(ValueError("Non-finite JSON number")), object_pairs_hook=unique_pairs)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid JSON input") from exc


def read_request(path: str | Path) -> dict:
    return validate_request(_bounded_json(Path(path), MAX_REQUEST_BYTES))


def _crate_metadata(task: dict, result: dict, publication_date: str | None = None, software_version: str | None = None) -> dict:
    """RO-Crate 1.3 core metadata; None preserves V1.1 legacy bundle checks."""
    return {"@context": "https://w3id.org/ro/crate/1.3/context", "@graph": [
        {"@id": "ro-crate-metadata.json", "@type": "CreativeWork",
         "conformsTo": {"@id": "https://w3id.org/ro/crate/1.3"}, "about": {"@id": "./"}},
        {"@id": "./", "@type": "Dataset", "name": "NeuroShield synthetic research task",
         "description": "Unvalidated S0 research artifact, no real human or lab data",
         **({"datePublished": publication_date,
             "license": "No output license is granted by this metadata; the NeuroShield software uses Apache-2.0."}
            if publication_date is not None else {}),
         "hasPart": [{"@id": "task.json"}, {"@id": "result.json"}, {"@id": "checksums.json"}]},
        {"@id": "task.json", "@type": "File", "encodingFormat": "application/json",
         "name": "Validated synthetic task"},
        {"@id": "result.json", "@type": "File", "encodingFormat": "application/json",
         "name": "Synthetic computational report"},
        {"@id": "checksums.json", "@type": "File", "encodingFormat": "application/json",
         "name": "Content integrity hashes"},
        {"@id": "#task-action", "@type": "CreateAction", "object": {"@id": "task.json"},
         "result": {"@id": "result.json"}, "instrument": {"@id": "#neuroshield"}},
        {"@id": "#neuroshield", "@type": "SoftwareApplication", "name": "NeuroShield agent_protocol",
         "description": "Offline fixed-operation synthetic research runner",
         **({"url": "https://github.com/sidhulyalkar/eeg-helmet",
              "version": __version__ if software_version is None else software_version} if publication_date is not None else {})},
    ]}


def create_bundle(request: object, destination: str | Path) -> dict:
    """Write one new synthetic-only bundle. Never overwrite an existing directory."""
    task = validate_request(request)
    report = execute(task)
    path = Path(destination)
    if path.exists() or path.is_symlink():
        raise FileExistsError("Output path already exists; refuse overwrite")
    path.mkdir(parents=False, exist_ok=False)
    task_bytes = _json_bytes(task)
    result_bytes = _json_bytes(report)
    # Publication date describes this export only; it is not part of the
    # reproducible task/result identity. A clock-independent historical task
    # remains scientifically comparable after a later export date.
    publication_date = datetime.now(timezone.utc).date().isoformat()
    crate_bytes = _json_bytes(_crate_metadata(task, report, publication_date))
    checksum = {"schema_version": "neuroshield.artifact-checksums/0.2", "files": {
        "task.json": hashlib.sha256(task_bytes).hexdigest(),
        "result.json": hashlib.sha256(result_bytes).hexdigest(),
        "ro-crate-metadata.json": hashlib.sha256(crate_bytes).hexdigest()}}
    (path / "task.json").write_bytes(task_bytes)
    (path / "result.json").write_bytes(result_bytes)
    (path / "ro-crate-metadata.json").write_bytes(crate_bytes)
    (path / "checksums.json").write_bytes(_json_bytes(checksum))
    return {"status": report["status"], "task_sha256": report["task_sha256"],
            "result_sha256": report["result_sha256"], "bundle_dir": str(path)}


def verify_bundle(path: str | Path) -> dict:
    """Validate local SHA integrity, NOT authenticity or independent physical evidence."""
    root = Path(path)
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Expected a bundle directory")
    check = _bounded_json(root / "checksums.json", 4096)
    if not isinstance(check, dict) or set(check) != {"schema_version", "files"} or check["schema_version"] not in ("neuroshield.artifact-checksums/0.1", "neuroshield.artifact-checksums/0.2") or not isinstance(check["files"], dict):
        raise ValueError("Invalid checksum manifest")
    legacy = check["schema_version"].endswith("/0.1")
    expected_files = {"task.json", "result.json"} if legacy else {"task.json", "result.json", "ro-crate-metadata.json"}
    if set(check["files"]) != expected_files:
        raise ValueError("Invalid checksum manifest")
    for file in sorted(expected_files):
        f = root / file
        if f.is_symlink() or not f.is_file() or f.stat().st_size > MAX_REPORT_BYTES:
            raise ValueError("Missing or unsafe artifact")
        if not isinstance(check["files"][file], str) or hashlib.sha256(f.read_bytes()).hexdigest() != check["files"][file]:
            raise ValueError(f"Artifact checksum mismatch: {file}")
    task = read_request(root / "task.json")
    report = _bounded_json(root / "result.json", MAX_REPORT_BYTES)
    if not isinstance(report, dict) or set(report) != {"schema_version","task_sha256","task_id","operation","source_sha256","data_class","scientific_evidence_level","status","result","limitations","result_sha256"}:
        raise ValueError("Unexpected report structure")
    receipt = report["result_sha256"]
    unsigned = {k:v for k,v in report.items() if k != "result_sha256"}
    if receipt != canonical_hash(unsigned) or report["task_sha256"] != canonical_hash(task) or report["task_id"] != task["task_id"] or report["operation"] != task["operation"]:
        raise ValueError("Task-result provenance mismatch")
    if report["scientific_evidence_level"] != "S0" or report["data_class"] != "SYNTHETIC_ONLY":
        raise ValueError("Evidence or data classification escalated")
    crate = _bounded_json(root / "ro-crate-metadata.json", 65536)
    published = None
    software_version = None
    if not legacy:
        try:
            graph = crate["@graph"]
            published = next(x for x in graph if x.get("@id") == "./")["datePublished"]
            if not isinstance(published, str) or date.fromisoformat(published).isoformat() != published:
                raise ValueError("Invalid RO-Crate publication date")
            software_version = next(x for x in graph if x.get("@id") == "#neuroshield")["version"]
            if not isinstance(software_version, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.+_-]{0,63}", software_version):
                raise ValueError("Invalid RO-Crate software version")
        except (KeyError, TypeError, StopIteration, ValueError, AttributeError) as exc:
            raise ValueError("Missing or invalid RO-Crate datePublished") from exc
    if crate != _crate_metadata(task, report, published, software_version):
        raise ValueError("RO-Crate metadata mismatch")
    return {"status": "LOCAL_INTEGRITY_VERIFIED_NOT_AUTHENTICATED", "scientific_evidence_level": "S0",
            "task_sha256": canonical_hash(task), "result_sha256": receipt}


def task_schema():
    """Bundled JSON Schema for external agent hosts; runtime gate remains authoritative."""
    return json.loads(files("neuroshield").joinpath("schemas/agent-task.schema.json").read_text(encoding="utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline synthetic research-agent protocol (not an MCP server)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("capabilities")
    sub.add_parser("schema")
    val = sub.add_parser("validate"); val.add_argument("task")
    run = sub.add_parser("run"); run.add_argument("task"); run.add_argument("--out", required=True)
    verify = sub.add_parser("verify"); verify.add_argument("bundle")
    args = parser.parse_args(argv)
    try:
        if args.command == "capabilities":
            result = capabilities()
        elif args.command == "schema":
            result = task_schema()
        elif args.command == "validate":
            task = read_request(args.task)
            result = {"status": "VALID_SYNTHETIC_TASK", "task_sha256": canonical_hash(task)}
        elif args.command == "run":
            result = create_bundle(read_request(args.task), args.out)
        else:
            result = verify_bundle(args.bundle)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
