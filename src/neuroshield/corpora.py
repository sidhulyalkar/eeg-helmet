"""Three offline, metadata-only scientific source catalogs for NeuroShield.

Links help researchers navigate relevant literature/standards. They are NOT
licensed redistributions, validation measurements, or scientific evidence for
any helmet claim. No network access, downloads, or patient data processing.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
import math
from pathlib import Path
import re
from urllib.parse import urlsplit

from .knowledge import KnowledgeError, _tokens, _run_git

SCHEMA = "neuroshield.corpora.v1"
DOMAINS = ("biomechanics", "neural", "evidence")
ACCESS_STATUS = "metadata_only"
LICENSE_STATUS = "pending_manual_review"
VERSION_TYPES = ("explicit_version", "dated_page", "living_page")
STATUS = "S0_EXTERNAL_CONTEXT_ONLY"
MAX_MANIFEST_BYTES = 128_000
MAX_NOTES = 480
SAFE_ID = re.compile(r"^[a-z][a-z0-9-]{2,63}$")


def _read(path: Path) -> dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_MANIFEST_BYTES:
        raise KnowledgeError(f"Missing, symlinked or oversized catalog: {path}")
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, ValueError, OSError) as exc:
        raise KnowledgeError(f"Cannot parse catalog: {path}") from exc
    if not isinstance(obj, dict):
        raise KnowledgeError("Catalog must be a JSON object")
    return obj


def _https(value: object) -> bool:
    if not isinstance(value, str) or len(value) > 700 or "\\" in value or any(ord(c) < 32 for c in value):
        return False
    try:
        u = urlsplit(value)
        return u.scheme == "https" and bool(u.hostname) and not u.username and not u.password and not u.fragment
    except ValueError:
        return False


def _positive_text(v: object, limit: int = MAX_NOTES, minimum: int = 3) -> bool:
    return isinstance(v, str) and minimum <= len(v.strip()) <= limit and "\x00" not in v


def load_catalog(root: str | Path) -> dict:
    """Fail closed on ambiguous provenance, permissions and claims."""
    root = Path(root).resolve()
    catalogs = {}
    ids, urls = set(), set()
    for domain in DOMAINS:
        path = root / "knowledge" / "corpora" / f"{domain}.json"
        obj = _read(path)
        if obj.get("schema") != SCHEMA or obj.get("domain") != domain:
            raise KnowledgeError(f"Unexpected schema/domain in {path.name}")
        entries = obj.get("sources")
        if not isinstance(entries, list) or not entries or len(entries) > 100:
            raise KnowledgeError(f"Expected 1..100 curated sources in {domain}")
        for src in entries:
            if not isinstance(src, dict):
                raise KnowledgeError("Invalid source record")
            sid = src.get("id")
            if not isinstance(sid, str) or not SAFE_ID.fullmatch(sid) or sid in ids:
                raise KnowledgeError(f"Duplicate/unsafe source id: {sid}")
            ids.add(sid)
            if src.get("corpus") != domain:
                raise KnowledgeError(f"Source in wrong corpus: {sid}")
            url = src.get("url")
            if not _https(url) or url in urls:
                raise KnowledgeError(f"Invalid/duplicate HTTPS URL: {sid}")
            urls.add(url)
            for field in ("title", "publisher", "relevance", "version"):
                if not _positive_text(src.get(field)):
                    raise KnowledgeError(f"Missing {field} in {sid}")
            if src.get("version_kind") not in VERSION_TYPES:
                raise KnowledgeError(f"Missing source revision classification in {sid}")
            if (src.get("access") != ACCESS_STATUS or src.get("license_status") != LICENSE_STATUS
                    or src.get("evidence_role") != "reference_only" or src.get("can_promote_evidence") is not False):
                raise KnowledgeError(f"Unreviewed source cannot authorize content import or evidence promotion: {sid}")
            if any(k in src for k in ("full_text", "raw_data", "content", "extracted_text", "local_path", "license_approved")):
                raise KnowledgeError(f"Raw content or unsupported permission claim in {sid}")
        catalogs[domain] = entries
    return catalogs


def load_links(root: str | Path, source_ids: set[str]) -> list[dict]:
    root = Path(root).resolve()
    links = _read(root / "knowledge" / "corpora" / "hypotheses.json")
    if links.get("schema") != SCHEMA or not isinstance(links.get("hypotheses"), list):
        raise KnowledgeError("Invalid research hypothesis registry")
    # The original S0 registry retains authority over implementation claims.
    legacy = _read(root / "knowledge" / "registry.json")
    claim_ids = {c["id"] for c in legacy.get("claims", [])}
    ids = set()
    for hypothesis in links["hypotheses"]:
        if not isinstance(hypothesis, dict) or not isinstance(hypothesis.get("id"), str):
            raise KnowledgeError("Invalid hypothesis")
        hid = hypothesis["id"]
        if not SAFE_ID.fullmatch(hid) or hid in ids:
            raise KnowledgeError(f"Duplicate/unsafe hypothesis: {hid}")
        ids.add(hid)
        refs = hypothesis.get("reference_ids")
        if not isinstance(refs, list) or not refs or any(x not in source_ids for x in refs):
            raise KnowledgeError(f"Unknown hypothesis references: {hid}")
        if not isinstance(hypothesis.get("claim_ids"), list) or any(x not in claim_ids for x in hypothesis["claim_ids"]):
            raise KnowledgeError(f"Unknown implementation claims: {hid}")
        if not _positive_text(hypothesis.get("test_to_run"), 700) or not _positive_text(hypothesis.get("blocker"), 700):
            raise KnowledgeError(f"Missing next experiment/limitations: {hid}")
        if hypothesis.get("evidence_tier") != "S0" or hypothesis.get("status") != "not_physically_validated":
            raise KnowledgeError(f"Hypothesis cannot be promoted via source registry: {hid}")
    return links["hypotheses"]


def audit(root: str | Path) -> dict:
    catalogs = load_catalog(root)
    ids = {x["id"] for entries in catalogs.values() for x in entries}
    hypotheses = load_links(root, ids)
    return {
        "schema": SCHEMA, "status": "PASS_METADATA_STRUCTURE_ONLY",
        "corpora": {k: len(v) for k, v in catalogs.items()},
        "reference_count": len(ids), "hypothesis_count": len(hypotheses),
        "clinical_authority": False, "physical_validation": False,
        "all_sources_license_pending": True, "max_evidence_tier": "S0",
        "warning": "Links and authored summaries are for navigation; URL reachability, accuracy and redistribution licenses are NOT checked."
    }


def list_sources(root: str | Path, domain: str = "all") -> dict:
    catalogs = load_catalog(root)
    if domain not in (*DOMAINS, "all"):
        raise KnowledgeError("Unknown domain")
    selected = [x for key, entries in catalogs.items() if domain in ("all", key) for x in entries]
    return {"schema": SCHEMA, "domain": domain, "sources": selected, "authority": STATUS}


def _rank(sources: list[dict], query: str, top_k: int) -> list[dict]:
    if not isinstance(query, str) or not query.strip() or len(query) > 500:
        raise KnowledgeError("Query must be 1..500 nonblank characters")
    if type(top_k) is not int or not (1 <= top_k <= 20):
        raise KnowledgeError("top_k must be 1..20")
    q = set(_tokens(query))
    if not q:
        return []
    fields = []
    for s in sources:
        parts = {
            "title": Counter(_tokens(s["title"])),
            "id": Counter(_tokens(s["id"])),
            "relevance": Counter(_tokens(s["relevance"])),
            "publisher": Counter(_tokens(s["publisher"])),
        }
        fields.append(parts)
    document_freq = Counter(w for parts in fields for w in set().union(*[set(p) for p in parts.values()]))
    results = []
    weights = {"title": 3.5, "id": 1.5, "relevance": 1.0, "publisher": .4}
    for s, parts in zip(sources, fields):
        score = 0.0
        for token in q:
            idf = math.log(1 + (len(sources) + 1)/(document_freq[token] + 1))
            score += idf * sum(weights[field] * (1 + math.log(counts[token])) for field, counts in parts.items() if counts[token])
        if score:
            results.append((score, s))
    results.sort(key=lambda x: (-x[0], x[1]["id"]))
    return [{"id": s["id"], "corpus": s["corpus"], "title": s["title"], "url": s["url"],
             "version": s["version"], "license_status": s["license_status"], "score": round(v, 6)}
            for v, s in results[:top_k]]


def search(root: str | Path, query: str, domain: str = "all", top_k: int = 5) -> dict:
    selected = list_sources(root, domain)["sources"]
    return {"schema": SCHEMA, "method": "curated_metadata_lexical_v1", "domain": domain, "query": query,
            "hits": _rank(selected, query, top_k), "authority": STATUS}


def benchmark(root: str | Path, top_k: int = 5) -> dict:
    root = Path(root).resolve()
    cases = _read(root / "knowledge" / "corpora" / "questions.json")
    if cases.get("schema") != SCHEMA or not isinstance(cases.get("questions"), list) or not cases["questions"]:
        raise KnowledgeError("Invalid frozen benchmark")
    catalogs = load_catalog(root)
    source_index = {s["id"]: s["corpus"] for group in catalogs.values() for s in group}
    ids = set()
    records = []
    for case in cases["questions"]:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str) or case["id"] in ids:
            raise KnowledgeError("Duplicate/invalid question")
        ids.add(case["id"])
        domain, expected = case.get("domain"), case.get("expected_ids")
        if domain not in DOMAINS or not isinstance(expected, list) or not expected or any(source_index.get(x) != domain for x in expected):
            raise KnowledgeError("Question expected IDs must belong to its domain")
        hits = search(root, case.get("query"), domain, top_k)["hits"]
        rank = next((i for i, h in enumerate(hits, 1) if h["id"] in expected), None)
        records.append({"id": case["id"], "domain": domain, "rank": rank, "expected_ids": expected,
                        "top_ids": [h["id"] for h in hits]})
    return {"schema": SCHEMA, "method": "curated_metadata_lexical_v1", "question_count": len(records),
            "hit_at_k": sum(x["rank"] is not None for x in records)/len(records),
            "mrr_at_k": sum((1/x["rank"] if x["rank"] else 0) for x in records)/len(records),
            "top_k": top_k, "details": records, "conclusion": "METADATA_RETRIEVAL_ONLY_NOT_SCIENTIFIC_VALIDATION"}


def qualification_gaps(root: str | Path) -> dict:
    catalogs = load_catalog(root)
    hypotheses = load_links(root, {x["id"] for group in catalogs.values() for x in group})
    return {"schema": SCHEMA, "status": "S0_UNVALIDATED", "physical_validation": False,
            "hypotheses": [{"id": h["id"], "claim_ids": h["claim_ids"],
                            "reference_ids": h["reference_ids"], "blocking_requirement": h["blocker"],
                            "next_experiment": h["test_to_run"], "evidence_tier": "S0"} for h in hypotheses]}


def stage_metadata(root: str | Path, destination: str | Path) -> dict:
    """Generate separate inspectable snapshots of authored metadata ONLY.

    This never fetches source URLs, imports standards, or copies third-party texts.
    """
    root = Path(root).resolve()
    dest = Path(destination).resolve()
    if dest == root or root in dest.parents or dest.exists():
        raise KnowledgeError("Staging directory must not exist and must be outside repository")
    catalogs = load_catalog(root)
    load_links(root, {x["id"] for group in catalogs.values() for x in group})
    # Enforce exactly the tracked HEAD snapshot, never modified/untracked notes.
    commit = _run_git(root, ["rev-parse", "--verify", "HEAD"]).decode().strip()
    for name in (*[f"knowledge/corpora/{d}.json" for d in DOMAINS],
                 "knowledge/corpora/hypotheses.json", "knowledge/registry.json"):
        try:
            committed = _run_git(root, ["show", f"HEAD:{name}"])
        except KnowledgeError as exc:
            raise KnowledgeError(f"Commit the catalog before staging: {name}") from exc
        checkout = (root / name).read_bytes()
        # Windows core.autocrlf may materialize CRLF for committed LF blobs.
        # Only canonicalize line endings; any substantive edit still fails.
        if committed != checkout.replace(b"\r\n", b"\n"):
            raise KnowledgeError(f"Catalog differs from committed HEAD: {name}")
    outputs = []
    for domain in DOMAINS:
        for src in catalogs[domain]:
            # Generate text entirely from human-curated metadata, never fetched documents.
            value = f"Source ID: {src['id']}\nTitle: {src['title']}\nPublisher: {src['publisher']}\n"
            value += f"Version: {src['version']} ({src['version_kind']})\nURL: {src['url']}\n"
            value += f"Research relevance: {src['relevance']}\n"
            value += "Evidence: EXTERNAL CONTEXT ONLY. License pending. Full text not present.\n"
            data = value.encode("utf-8")
            outputs.append((domain, src["id"], data))
    dest.mkdir(parents=True, mode=0o700)
    manifest = {"schema": SCHEMA, "scope": "authored_metadata_only_no_third_party_content", "corpora": {},
                "clinical_authority": False, "physical_validation": False, "source_count": len(outputs), "repository_commit": commit}
    for domain, sid, data in outputs:
        folder = dest / domain
        folder.mkdir(exist_ok=True, mode=0o700)
        path = folder / (sid + ".txt")
        path.write_bytes(data)
        path.chmod(0o600)
        manifest["corpora"].setdefault(domain, []).append({"file": f"{domain}/{sid}.txt", "sha256": sha256(data).hexdigest()})
    manifest_file = dest / "CORPORA-MANIFEST.json"
    manifest_file.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest_file.chmod(0o600)
    return {"status": "STAGED_METADATA_ONLY", "path": str(dest), "source_count": len(outputs), "repository_commit": commit,
            "corpora": {d: len(catalogs[d]) for d in DOMAINS},
            "sha256": sha256(manifest_file.read_bytes()).hexdigest(),
            "optional_index_commands": [f"xerj autoindex {dest / d} --prefix eeg-helmet-{d}" for d in DOMAINS]}
