"""Read-only map from research questions to code, tests and evidence boundaries.

Navigation for researchers and agents, never a command executor, data importer,
model qualifier, or authority to change scientific evidence tiers.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path, PurePosixPath

SCHEMA = "neuroshield.research-workflows/0.1"
AUTHORITY = "CURATED_DISCOVERY_ONLY_NO_EVIDENCE_PROMOTION"
READINESS = {"synthetic_runnable", "metadata_review_only", "structural_review_only",
             "synthetic_or_local_review_only", "prototype_visualization"}
INPUT_CLASSES = {"synthetic_only", "public_metadata_only", "declared_nonhuman_or_synthetic"}
FIELDS = {"id", "question", "software_readiness", "input_class", "evidence_tier",
          "example_command", "code", "tests", "protocol", "related_claim_ids",
          "not_established"}
IDENTIFIER = re.compile(r"[a-z][a-z0-9-]{2,63}\Z")
MAX_BYTES = 65_536
UNMAPPED_CODE_EXCEPTIONS = {"__init__.py", "__main__.py", "research_map.py"}


def _duplicates_forbidden(pairs):
    record = {}
    for key, value in pairs:
        if key in record:
            raise ValueError("Duplicate JSON field in research map")
        record[key] = value
    return record


def _load(path: Path):
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= MAX_BYTES:
        raise ValueError("Missing, symlinked or oversized research metadata")
    try:
        return json.loads(path.read_text(encoding="utf-8"),
                          object_pairs_hook=_duplicates_forbidden,
                          parse_constant=lambda _: (_ for _ in ()).throw(
                              ValueError("Non-finite research metadata")))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid research map JSON") from exc


def _checked_path(root: Path, value: str, group: str) -> str:
    if not isinstance(value, str) or "\\" in value or "%" in value or "\x00" in value:
        raise ValueError("Invalid research path")
    rel = PurePosixPath(value)
    parts = rel.parts
    if (rel.is_absolute() or not parts or ".." in parts or "." in parts
            or value != rel.as_posix() or any(p.startswith(".") for p in parts)):
        raise ValueError("Unsafe research path")
    if group == "code":
        allowed = len(parts) == 3 and parts[:2] == ("src", "neuroshield") and rel.suffix == ".py"
    elif group == "tests":
        allowed = len(parts) == 2 and parts[0] == "tests" and rel.name.startswith("test_") and rel.suffix == ".py"
    else:
        allowed = len(parts) == 2 and parts[0] in ("docs", "cad") and rel.suffix == ".md"
    if not allowed:
        raise ValueError("Unexpected research path category")
    cursor = root
    for part in parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError("Symlinked research path")
    if not cursor.is_file() or not cursor.resolve().is_relative_to(root):
        raise ValueError("Missing or escaped research source")
    return value


def load_workflows(root: str | Path = ".") -> list[dict]:
    """Fail closed on stale owner links and unsupported evidence or execution claims."""
    root = Path(root).resolve()
    record = _load(root / "knowledge" / "research-workflows.json")
    if (not isinstance(record, dict) or set(record) !=
            {"schema_version", "authority", "scientific_evidence_ceiling", "workflows"}
            or record["schema_version"] != SCHEMA
            or record["authority"] != AUTHORITY
            or record["scientific_evidence_ceiling"] != "S0"):
        raise ValueError("Invalid research map authority or evidence ceiling")
    claims = _load(root / "knowledge" / "registry.json")
    if claims.get("schema") != "neuroshield.knowledge.v1":
        raise ValueError("Missing canonical claim registry")
    claim_ids = {x["id"] for x in claims["claims"] if x.get("evidence_tier") == "S0"}
    items = record["workflows"]
    if not isinstance(items, list) or not 1 <= len(items) <= 24:
        raise ValueError("Expected 1..24 research workflows")
    seen, module_paths = set(), set()
    for item in items:
        if not isinstance(item, dict) or set(item) != FIELDS:
            raise ValueError("Research workflow requires exact fields")
        uid = item["id"]
        if not isinstance(uid, str) or not IDENTIFIER.fullmatch(uid) or uid in seen:
            raise ValueError("Duplicate or unsafe workflow identifier")
        seen.add(uid)
        if (item["software_readiness"] not in READINESS or
                item["input_class"] not in INPUT_CLASSES or item["evidence_tier"] != "S0"):
            raise ValueError("Research readiness and evidence must remain separately S0")
        for name in ("question", "not_established"):
            value = item[name]
            if not isinstance(value, str) or not 30 <= len(value) <= 500 or "\n" in value:
                raise ValueError("Research question and limitation must be substantive")
        command = item["example_command"]
        if (not isinstance(command, str) or len(command) > 400
                or not command.startswith("python -m neuroshield")
                or any(ch in command for ch in "\n\r;|&$<>")):
            raise ValueError("Unsafe example command (display only; never executed)")
        for group in ("code", "tests"):
            paths = item[group]
            if not isinstance(paths, list) or not paths or len(paths) > 15 or len(set(paths)) != len(paths):
                raise ValueError("Missing or duplicate owner paths")
            for path in paths:
                _checked_path(root, path, group)
                if group == "code":
                    module_paths.add(path)
        _checked_path(root, item["protocol"], "protocol")
        claim_list = item["related_claim_ids"]
        if (not isinstance(claim_list, list) or not claim_list
                or len(set(claim_list)) != len(claim_list)
                or any(not isinstance(c, str) or c not in claim_ids for c in claim_list)):
            raise ValueError("Related claims must be existing S0 registry claims")
    source_dir = root / "src" / "neuroshield"
    required = {p.relative_to(root).as_posix() for p in source_dir.glob("*.py")
                if p.name not in UNMAPPED_CODE_EXCEPTIONS}
    missing = sorted(required - module_paths)
    if missing:
        raise ValueError("Unmapped public source modules: " + ", ".join(missing))
    return items


def audit(root: str | Path = ".") -> dict:
    items = load_workflows(root)
    return {"schema_version": SCHEMA,
            "status": "NAVIGATION_LINKS_VERIFIED_NOT_SCIENTIFIC_EVIDENCE",
            "workflow_count": len(items),
            "mapped_module_count": len({p for x in items for p in x["code"]}),
            "scientific_evidence_ceiling": "S0",
            "permissions_granted": False,
            "external_physical_validation": False}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Offline NeuroShield scientific research map")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("audit", "list", "show"):
        p = sub.add_parser(name)
        p.add_argument("--root", default=".")
        if name == "show":
            p.add_argument("id")
    args = parser.parse_args(argv)
    try:
        if args.command == "audit":
            result = audit(args.root)
        else:
            items = load_workflows(args.root)
            if args.command == "list":
                result = {"schema_version": SCHEMA, "authority": AUTHORITY,
                          "scientific_evidence_ceiling": "S0",
                          "workflows": [{"id": x["id"], "question": x["question"],
                                         "software_readiness": x["software_readiness"]}
                                        for x in items]}
            else:
                result = next((x for x in items if x["id"] == args.id), None)
                if result is None:
                    raise ValueError("Unknown research workflow identifier")
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    except (ValueError, OSError, TypeError, KeyError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
