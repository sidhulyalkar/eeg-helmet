"""An offline, failure-preserving reproduction exercise for outside researchers.

Only two built-in S0 synthetic tasks are permitted. No network, human recordings,
user-supplied code, or arbitrary command execution. An exercise is not evidence
that an independent person has performed it.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

from .agent_protocol import SCHEMA, _bounded_json, create_bundle, read_request, validate_request
from .provenance import canonical_hash
from .reproduction import replay_bundle

VERSION = "neuroshield.reproduction-challenge/0.1"
REPORT_NAME = "challenge-report.json"
CASES = (
    ("impact", "simulate_synthetic", {"scenario": "oblique", "parameters": {}}),
    ("numerics", "audit_synthetic_numerics", {"scenario": "all"}),
)
PASS_STATUSES = {"REPRODUCED_EXACT", "REPRODUCED_WITHIN_NUMERICAL_TOLERANCE"}
MAX_REPORT_BYTES = 16_384


def _task(case_id: str, operation: str, inputs: dict) -> dict:
    return {"schema_version": SCHEMA, "task_id": "repro-" + case_id,
            "data_class": "SYNTHETIC_ONLY", "operation": operation, "inputs": inputs}


def _case_error(exc: Exception, phase: str) -> str:
    # Never export exception messages or paths; they may disclose local metadata.
    if type(exc) in (ValueError, TypeError, KeyError, FileExistsError):
        return phase + "_INVALID_ARTIFACT"
    return phase + "_EXECUTION_ERROR"


def run_challenge(destination: str | Path, *, bundle_runner=None, replay_runner=None) -> dict:
    """Attempt every fixed case, preserving failure outcomes without deleting artifacts.

    Runner injection is for unit tests; the public CLI never accepts runner names.
    """
    bundle_runner = create_bundle if bundle_runner is None else bundle_runner
    replay_runner = replay_bundle if replay_runner is None else replay_runner
    root = Path(destination)
    if root.exists() or root.is_symlink():
        raise FileExistsError("Exercise destination already exists")
    root.mkdir(parents=False, exist_ok=False)
    cases = []
    for case_id, operation, inputs in CASES:
        record = {"case_id": case_id, "operation": operation,
                  "status": "FAILED", "replay_status": "NOT_ATTEMPTED",
                  "task_sha256": None, "result_sha256": None, "error_code": None}
        try:
            receipt = bundle_runner(_task(case_id, operation, inputs), root / case_id)
            # The recorded hash is taken from the bundle, not inferred from intentions.
            record["task_sha256"] = receipt["task_sha256"]
            record["result_sha256"] = receipt["result_sha256"]
            observed = replay_runner(root / case_id)
            record["replay_status"] = observed["status"]
            if (observed["status"] in PASS_STATUSES and
                    observed["task_sha256"] == record["task_sha256"] and
                    observed["recorded_result_sha256"] == record["result_sha256"]):
                record["status"] = "PASS_COMPUTATIONAL_ONLY"
            else:
                record["error_code"] = "REPLAY_NOT_REPRODUCED"
        except (OSError, ValueError, TypeError, KeyError) as exc:
            record["error_code"] = _case_error(exc, "CASE")
        cases.append(record)
    all_pass = all(case["status"] == "PASS_COMPUTATIONAL_ONLY" for case in cases)
    report = {
        "schema_version": VERSION,
        "status": "PASS_COMPUTATIONAL_ONLY" if all_pass else "FAILURES_RETAINED",
        "scientific_evidence_level": "S0",
        "environment_declaration": {"python": f"{sys.version_info.major}.{sys.version_info.minor}",
                                    "os_family": platform.system().lower()},
        "cases": cases,
        "independent_human_reproduction": "NOT_ESTABLISHED",
        "note": "Deterministic synthetic tests only; no independent human review, source authenticity, or physical/clinical validation.",
    }
    (root / REPORT_NAME).write_text(json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    return report


def verify_challenge(destination: str | Path, *, replay_runner=None) -> dict:
    """Read-only re-evaluation. A rehashed but fabricated scientific report cannot pass."""
    replay_runner = replay_bundle if replay_runner is None else replay_runner
    root = Path(destination)
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Expected non-symlink exercise directory")
    report = _bounded_json(root / REPORT_NAME, MAX_REPORT_BYTES)
    required = {"schema_version", "status", "scientific_evidence_level", "environment_declaration",
                "cases", "independent_human_reproduction", "note"}
    if not isinstance(report, dict) or set(report) != required or report["schema_version"] != VERSION:
        raise ValueError("Unsupported or malformed challenge report")
    if report["scientific_evidence_level"] != "S0" or report["independent_human_reproduction"] != "NOT_ESTABLISHED":
        raise ValueError("Forbidden evidence or independence escalation")
    if not isinstance(report["cases"], list) or len(report["cases"]) != len(CASES):
        raise ValueError("Challenge must retain all fixed cases")
    expected_root = {REPORT_NAME, *(case_id for case_id, _, _ in CASES)}
    if not {p.name for p in root.iterdir()} <= expected_root:
        raise ValueError("Unexpected files in exercise directory")
    findings = []
    for stored, (case_id, operation, inputs) in zip(report["cases"], CASES):
        fields = {"case_id", "operation", "status", "replay_status", "task_sha256", "result_sha256", "error_code"}
        if not isinstance(stored, dict) or set(stored) != fields or stored["case_id"] != case_id or stored["operation"] != operation:
            raise ValueError("Case identity or fields altered")
        if stored["status"] != "PASS_COMPUTATIONAL_ONLY":
            findings.append({"case_id": case_id, "status": "RECORDED_FAILURE", "replay_status": "NOT_ELIGIBLE"})
            continue
        bundle = root / case_id
        if bundle.is_symlink() or not bundle.is_dir():
            findings.append({"case_id": case_id, "status": "FAILED_BUNDLE_MISSING", "replay_status": "NOT_ATTEMPTED"})
            continue
        try:
            saved_task = read_request(bundle / "task.json")
            if saved_task != validate_request(_task(case_id, operation, inputs)):
                findings.append({"case_id": case_id, "status": "FAILED_TASK_CONTRACT",
                                 "replay_status": "NOT_ATTEMPTED"})
                continue
            observed = replay_runner(bundle)
            match = (observed["status"] == stored["replay_status"] and
                     observed["status"] in PASS_STATUSES and
                     observed["task_sha256"] == stored["task_sha256"] and
                     observed["recorded_result_sha256"] == stored["result_sha256"])
            findings.append({"case_id": case_id, "status": "PASS_COMPUTATIONAL_ONLY" if match else "FAILED_REPLAY_MISMATCH",
                             "replay_status": observed["status"]})
        except (OSError, ValueError, TypeError, KeyError) as exc:
            findings.append({"case_id": case_id, "status": "FAILED_VERIFICATION",
                             "replay_status": _case_error(exc, "VERIFY")})
    all_pass = all(item["status"] == "PASS_COMPUTATIONAL_ONLY" for item in findings)
    # Comparison to the saved overall verdict catches a manipulated all-pass statement.
    if report["status"] not in ("PASS_COMPUTATIONAL_ONLY", "FAILURES_RETAINED") or (report["status"] == "PASS_COMPUTATIONAL_ONLY") != all(case["status"] == "PASS_COMPUTATIONAL_ONLY" for case in report["cases"]):
        raise ValueError("Exercise summary inconsistent with preserved cases")
    return {"schema_version": VERSION, "status": "PASS_COMPUTATIONAL_ONLY" if all_pass else "NOT_REPRODUCED",
            "scientific_evidence_level": "S0", "cases": findings,
            "exercise_report_sha256": canonical_hash(report),
            "independent_human_reproduction": "NOT_ESTABLISHED"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Offline failure-preserving NeuroShield reproduction exercise")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "verify"):
        sub.add_parser(name).add_argument("directory", type=Path)
    args = parser.parse_args(argv)
    try:
        result = run_challenge(args.directory) if args.command == "run" else verify_challenge(args.directory)
    except (ValueError, OSError, TypeError, KeyError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0 if result["status"] == "PASS_COMPUTATIONAL_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
