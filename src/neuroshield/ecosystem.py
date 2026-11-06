"""Read-only, offline navigation through external EEG research projects.

This metadata catalog grants no third-party reuse permission, scientific
evidence promotion, recording authority, hardware approval, or network access.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

SCHEMA = "neuroshield.eeg-ecosystem.v1"
AUTHORITY = "REFERENCE_ONLY_NO_REUSE_PERMISSION"
CATEGORIES = {
    "headwear", "acquisition_hardware", "acquisition_software", "streaming",
    "analysis", "benchmark", "data_standard", "data_archive", "cad",
    "retrieval", "community", "research_literature",
}
OPENNESS = {
    "open_hardware_reference", "open_source_reference", "open_standard",
    "public_data_platform", "community", "hosted_service",
    "public_research_reference",
}
FIELDS = {
    "id", "title", "category", "openness", "url", "utility",
    "limitation", "license_review", "evidence_role", "reuse_authorized",
}
IDENTIFIER = re.compile(r"[a-z][a-z0-9-]{2,63}\Z")
TOKEN = re.compile(r"[a-z0-9]+")
MAX_FILE_BYTES = 96_000


class EcosystemError(ValueError):
    """Malformed or unreviewed ecosystem reference metadata."""


def _unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise EcosystemError("Duplicate JSON property")
        obj[key] = value
    return obj


def _text(value, maximum=600):
    return (isinstance(value, str) and 12 <= len(value.strip()) <= maximum
            and all(ord(character) >= 32 for character in value))


def _url(value):
    if not isinstance(value, str) or len(value) > 800 or any(ord(c) < 33 for c in value):
        return False
    try:
        parsed = urlsplit(value)
        return (parsed.scheme == "https" and bool(parsed.hostname)
                and not parsed.username and not parsed.password
                and not parsed.fragment and parsed.port in (None, 443))
    except ValueError:
        return False


def load_catalog(root="."):
    """Validate an authored reference list; never retrieve any URLs or files."""
    root = Path(root).resolve()
    path = root / "knowledge" / "ecosystem" / "projects.json"
    if (path.is_symlink() or not path.is_file()
            or not 0 < path.stat().st_size <= MAX_FILE_BYTES):
        raise EcosystemError("Missing, symlinked, empty or oversized ecosystem catalog")
    try:
        obj = json.loads(path.read_text("utf-8"), object_pairs_hook=_unique_object,
                         parse_constant=lambda _: (_ for _ in ()).throw(
                             EcosystemError("Non-finite metadata")))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EcosystemError("Invalid ecosystem catalog JSON") from exc
    if (not isinstance(obj, dict) or set(obj) !=
            {"schema", "authority", "catalog_date", "entries"}
            or obj["schema"] != SCHEMA or obj["authority"] != AUTHORITY
            or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(obj["catalog_date"]))):
        raise EcosystemError("Unexpected ecosystem schema or authority")
    entries = obj["entries"]
    if not isinstance(entries, list) or not 5 <= len(entries) <= 100:
        raise EcosystemError("Expected 5..100 curated reference entries")
    seen_ids, seen_urls = set(), set()
    for item in entries:
        if not isinstance(item, dict) or set(item) != FIELDS:
            raise EcosystemError("Entry requires exact reference-only fields")
        uid = item["id"]
        if not isinstance(uid, str) or not IDENTIFIER.fullmatch(uid) or uid in seen_ids:
            raise EcosystemError("Duplicate or unsafe project ID")
        seen_ids.add(uid)
        url = item["url"]
        if not _url(url) or url in seen_urls:
            raise EcosystemError("Invalid or duplicate HTTPS reference URL")
        seen_urls.add(url)
        if item["category"] not in CATEGORIES or item["openness"] not in OPENNESS:
            raise EcosystemError("Unsupported project category or openness")
        if not all(_text(item[k]) for k in ("title", "utility", "limitation")):
            raise EcosystemError("Uninformative project title, utility or limitation")
        if (item["license_review"] != "pending_file_level"
                or item["evidence_role"] != "reference_only"
                or item["reuse_authorized"] is not False):
            raise EcosystemError("Catalog entries cannot grant source reuse or scientific evidence")
    return obj


def audit(root="."):
    obj = load_catalog(root)
    counts = {category: sum(1 for entry in obj["entries"]
                            if entry["category"] == category)
              for category in sorted(CATEGORIES)}
    return {"schema": SCHEMA, "status": "PASS_STRUCTURE_ONLY",
            "authority": AUTHORITY, "catalog_date": obj["catalog_date"],
            "project_count": len(obj["entries"]), "categories": counts,
            "license_reuse_authorized": False, "external_evidence_validated": False,
            "network_checks_performed": False,
            "warning": "Metadata reviewed for structure, not current availability, safety, scientific validity or file-level license."}


def find(root=".", *, category=None, query=None, project_id=None):
    obj = load_catalog(root)
    if category is not None and category not in CATEGORIES:
        raise EcosystemError("Unknown ecosystem category")
    items = [x for x in obj["entries"] if category is None or x["category"] == category]
    if project_id is not None:
        hits = [x for x in items if x["id"] == project_id]
        if not hits:
            raise EcosystemError("Unknown ecosystem project ID")
        return hits
    if query is None:
        return sorted(items, key=lambda x: x["id"])
    if not isinstance(query, str) or not query.strip() or len(query) > 300:
        raise EcosystemError("Query must contain 1..300 characters")
    terms = set(TOKEN.findall(query.lower()))
    if not terms:
        raise EcosystemError("Query has no searchable terms")
    scores = []
    for item in items:
        score = sum(
            weight * len(terms.intersection(TOKEN.findall(item[key].lower())))
            for key, weight in (("title", 4), ("category", 3),
                                ("utility", 2), ("limitation", 1))
        )
        if score:
            scores.append((score, item["id"], item))
    return [row[2] for row in sorted(scores, key=lambda v: (-v[0], v[1]))]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline, non-authoritative EEG ecosystem references")
    sub = parser.add_subparsers(dest="command", required=True)
    for cmd in ("audit", "list", "show", "search"):
        p = sub.add_parser(cmd)
        p.add_argument("--root", default=".")
        if cmd == "list" or cmd == "search":
            p.add_argument("--category", choices=sorted(CATEGORIES))
        if cmd == "show":
            p.add_argument("project_id")
        if cmd == "search":
            p.add_argument("query")
    args = parser.parse_args(argv)
    try:
        if args.command == "audit":
            report = audit(args.root)
        elif args.command == "show":
            report = {"authority": AUTHORITY,
                      "project": find(args.root, project_id=args.project_id)[0]}
        elif args.command == "search":
            report = {"authority": AUTHORITY, "query": args.query,
                      "hits": find(args.root, query=args.query, category=args.category)}
        else:
            report = {"authority": AUTHORITY, "projects":
                      find(args.root, category=args.category)}
        print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    except (EcosystemError, ValueError, OSError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
