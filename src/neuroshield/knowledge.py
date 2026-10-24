"""Offline evidence registry and committed-source retrieval staging.

Retrieval is a navigation aid, not scientific or clinical authority. No network
requests, human data, non-committed files, or optional XERJ imports occur here.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import subprocess
from collections import Counter

SCHEMA = "neuroshield.knowledge.v1"
EVIDENCE_TIERS = {"S0", "S1", "S2", "S3", "S4"}
SOURCE_TYPES = {"code", "test", "protocol", "documentation", "external_reference"}
CLAIM_TYPES = {"implementation", "model_assumption", "numerical_qualification", "future_research"}
ALLOWED_EXT = {".md", ".py", ".scad", ".toml", ".yml", ".yaml", ".json"}
MAX_FILE_BYTES = 256_000
MAX_CORPUS_BYTES = 2_000_000
CANDIDATE_RE = re.compile(r"[A-Za-z][A-Za-z0-9_/-]{1,}")
STOP = {"a", "an", "and", "are", "as", "by", "can", "do", "for", "from", "how", "in", "is", "it", "of", "on", "or", "our", "the", "this", "to", "what", "where", "which", "with", "we"}


class KnowledgeError(ValueError):
    """Invalid curated registry, corpus, or explicitly requested operation."""


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_path(value: str) -> bool:
    """Allow only a narrow, public-source subset. Data and hidden paths excluded."""
    if not isinstance(value, str) or "\\" in value or "\x00" in value:
        return False
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        return False
    if any(p.startswith(".") for p in path.parts):
        return False
    if path.suffix.lower() not in ALLOWED_EXT:
        return False
    if value in {"README.md", "CONTRIBUTING.md", "SECURITY.md", "CHANGELOG.md", "AGENTS.md", "pyproject.toml"}:
        return True
    if path.parts[0] == "src":
        return len(path.parts) >= 3 and path.parts[1] == "neuroshield" and (path.suffix == ".py" or (len(path.parts) >= 4 and path.parts[2] == "web" and path.suffix == ".md"))
    if path.parts[0] == "tests":
        return len(path.parts) == 2 and path.name.startswith("test_") and path.suffix == ".py"
    if path.parts[0] == "docs":
        return len(path.parts) == 2 and path.suffix == ".md"
    if path.parts[0] == "knowledge":
        return False  # Prevent answers and curated source-map leakage into retrieval tests.
    if path.parts[0] == "cad":
        return len(path.parts) == 2 and path.suffix in {".scad", ".md"}
    return False


def _load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise KnowledgeError(f"Cannot read JSON {path}: {exc}") from exc


def audit(root: str | Path) -> dict:
    """Check registry assertions against current local code, not medical evidence."""
    root = Path(root).resolve()
    registry = _load_json(root / "knowledge" / "registry.json")
    if not isinstance(registry, dict) or registry.get("schema") != SCHEMA:
        raise KnowledgeError("Registry schema must be neuroshield.knowledge.v1")
    sources = registry.get("sources")
    claims = registry.get("claims")
    if not isinstance(sources, list) or not isinstance(claims, list) or not sources or not claims:
        raise KnowledgeError("Nonempty sources and claims arrays required")
    source_ids = set()
    source_index = {}
    for src in sources:
        if not isinstance(src, dict) or not isinstance(src.get("id"), str) or src["id"] in source_ids:
            raise KnowledgeError("Invalid or duplicate source ID")
        source_ids.add(src["id"])
        source_index[src["id"]] = src
        if src.get("kind") not in SOURCE_TYPES:
            raise KnowledgeError(f"Unknown source kind: {src['id']}")
        if src["kind"] == "external_reference":
            if not src.get("url") or src.get("license_review") != "pending":
                raise KnowledgeError("External references require a URL and pending license review; not imported")
        else:
            path = src.get("path", "")
            if not _safe_path(path):
                raise KnowledgeError(f"Excluded or unsafe evidence path: {path}")
            item = root / path
            if not item.is_file() or item.is_symlink() or not item.resolve().is_relative_to(root):
                raise KnowledgeError(f"Missing, symlinked or escaped source: {path}")
    claim_ids = set()
    for claim in claims:
        if not isinstance(claim, dict) or not isinstance(claim.get("id"), str) or claim["id"] in claim_ids:
            raise KnowledgeError("Invalid or duplicate claim ID")
        claim_ids.add(claim["id"])
        if claim.get("kind") not in CLAIM_TYPES or claim.get("evidence_tier") not in EVIDENCE_TIERS:
            raise KnowledgeError(f"Invalid claim kind/evidence: {claim['id']}")
        if claim.get("evidence_tier") != "S0":
            raise KnowledgeError(f"Evidence promotion must be separately reviewed: {claim['id']}")
        if claim.get("inference_scope") != "synthetic_research_only":
            raise KnowledgeError(f"Unsafe inference scope: {claim['id']}")
        if not isinstance(claim.get("limitations"), str) or len(claim["limitations"].strip()) < 15:
            raise KnowledgeError(f"Claim requires explicit limitations: {claim['id']}")
        if not isinstance(claim.get("statement"), str) or len(claim["statement"].strip()) < 12:
            raise KnowledgeError(f"Claim requires a substantive statement: {claim['id']}")
        ids = claim.get("source_ids")
        if not isinstance(ids, list) or not ids or any(i not in source_ids for i in ids):
            raise KnowledgeError(f"Unresolved sources for claim: {claim['id']}")
        if all(source_index[i]["kind"] == "external_reference" for i in ids):
            raise KnowledgeError(f"External links alone cannot verify implementation: {claim['id']}")
    return {"schema": SCHEMA, "status": "PASS_REGISTRY_STRUCTURE_ONLY", "source_count": len(sources), "claim_count": len(claims), "max_evidence_tier": "S0", "clinical_authority": False}


def _run_git(root: Path, args: list[str]) -> bytes:
    try:
        p = subprocess.run(["git", "-C", str(root), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, timeout=20)
        return p.stdout
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise KnowledgeError(f"Committed Git revision required: {exc}") from exc


def committed_sources(root: str | Path) -> tuple[str, list[tuple[str, bytes]]]:
    """Read Git blobs at HEAD, not potentially private worktree/untracked files."""
    root = Path(root).resolve()
    commit = _run_git(root, ["rev-parse", "--verify", "HEAD"]).decode().strip()
    raw = _run_git(root, ["ls-tree", "-rz", "--full-tree", "HEAD"])
    result = []
    total = 0
    for item in raw.split(b"\x00"):
        if not item:
            continue
        try:
            descriptor, raw_path = item.split(b"\t", 1)
            mode, kind, sha = descriptor.decode("ascii").split(" ")
            path = raw_path.decode("utf-8")
        except (UnicodeDecodeError, ValueError) as exc:
            raise KnowledgeError("Invalid Git tree entry") from exc
        if not _safe_path(path):
            continue
        if mode != "100644" and mode != "100755":
            raise KnowledgeError(f"Refusing non-regular committed source: {path}")
        if kind != "blob":
            raise KnowledgeError(f"Refusing non-blob committed source: {path}")
        content = _run_git(root, ["cat-file", "blob", sha])
        if len(content) > MAX_FILE_BYTES or total + len(content) > MAX_CORPUS_BYTES:
            raise KnowledgeError(f"Corpus size limit exceeded at {path}")
        if b"\x00" in content:
            raise KnowledgeError(f"Binary content rejected: {path}")
        try:
            content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise KnowledgeError(f"Non-UTF8 content rejected: {path}") from exc
        total += len(content)
        result.append((path, content))
    if not result:
        raise KnowledgeError("No committed allowlisted sources found")
    return commit, result


def stage(root: str | Path, destination: str | Path) -> dict:
    """Materialize a private, inspectable allowlisted committed snapshot for XERJ."""
    root = Path(root).resolve()
    dest = Path(destination).resolve()
    if dest == root or root in dest.parents:
        raise KnowledgeError("Staging destination must be outside the repository")
    if dest.exists():
        raise KnowledgeError("Staging destination must not already exist; refusing overwrite")
    audit(root)
    commit, files = committed_sources(root)
    dest.mkdir(mode=0o700, parents=True)
    manifest = {"schema": SCHEMA, "repository_commit": commit, "scope": "allowlisted_committed_files_only", "clinical_authority": False, "file_count": len(files), "files": []}
    for relative, data in files:
        out = dest / relative
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        manifest["files"].append({"path": relative, "sha256": _digest(data), "bytes": len(data)})
    (dest / "CORPUS-MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"status": "STAGED_COMMITTED_CODE_ONLY", "commit": commit, "path": str(dest), "files": len(files), "sha256": _digest(json.dumps(manifest, sort_keys=True).encode()), "next_optional_step": f"xerj autoindex {str(dest)!r} --prefix eeg-helmet"}


def _tokens(s: str) -> list[str]:
    # Break up Python identifiers and paths so search terms match symbol names.
    tokens = []
    for w in CANDIDATE_RE.findall(s):
        for part in re.split(r"[_/-]+", w.lower()):
            if part and part not in STOP:
                tokens.append(part)
    return tokens


def _load_stage(path: Path):
    manifest = _load_json(path / "CORPUS-MANIFEST.json")
    if not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA:
        raise KnowledgeError("Missing valid staged corpus manifest")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise KnowledgeError("Empty corpus manifest")
    chunks = []
    for file in files:
        rel = file.get("path", "")
        if not _safe_path(rel):
            raise KnowledgeError(f"Unsafe staged path: {rel}")
        full = path / rel
        if not full.is_file() or full.is_symlink() or not full.resolve().is_relative_to(path.resolve()):
            raise KnowledgeError(f"Missing/escaped corpus file {rel}")
        data = full.read_bytes()
        if len(data) > MAX_FILE_BYTES or _digest(data) != file.get("sha256"):
            raise KnowledgeError(f"Staged source changed: {rel}")
        for line_no, line in enumerate(data.decode("utf-8").splitlines(), 1):
            if line.strip():
                chunks.append((rel, line_no, line))
    return manifest, chunks


def search(stage_dir: str | Path, query: str, top_k: int = 5) -> dict:
    """Deliberately simple and auditable lexical baseline, not semantic search."""
    if not isinstance(query, str) or not query.strip():
        raise KnowledgeError("Search query must be nonempty")
    if not isinstance(top_k, int) or not 1 <= top_k <= 20:
        raise KnowledgeError("top_k must be in [1,20]")
    manifest, chunks = _load_stage(Path(stage_dir))
    query_terms = _tokens(query)
    if not query_terms:
        return {"query": query, "method": "transparent_lexical_baseline", "commit": manifest["repository_commit"], "hits": []}
    docs = [(_tokens(path + " " + line), path, n, line) for path, n, line in chunks]
    freqs = Counter(w for toks, _, _, _ in docs for w in set(toks))
    N = len(docs)
    scored = []
    for words, path, line_no, line in docs:
        counts = Counter(words)
        score = sum((1 + math.log(counts[t])) * math.log(1 + (N + 1) / (freqs[t] + 1)) for t in query_terms if counts[t])
        if score <= 0:
            continue
        # More distinct covered query terms is important for troubleshooting.
        distinct = len(set(query_terms).intersection(counts))
        score = score * (1 + 0.18 * distinct)
        scored.append((score, path, line_no, line))
    scored.sort(key=lambda x: (-x[0], x[1], x[2]))
    # Return distinct owner files, not five adjacent matches in one large file.
    hits = []
    seen = set()
    for value, path, line_no, line in scored:
        if path in seen:
            continue
        seen.add(path)
        hits.append({"path": path, "line": line_no, "text": line[:350], "score": round(value, 6)})
        if len(hits) >= top_k:
            break
    return {"query": query, "method": "transparent_lexical_baseline", "commit": manifest["repository_commit"], "hits": hits}


def benchmark(root: str | Path, stage_dir: str | Path, k: int = 5) -> dict:
    """Use frozen natural-language owner questions, no model calls or learned weights."""
    questions = _load_json(Path(root) / "knowledge" / "questions.json")
    if not isinstance(questions, dict) or questions.get("schema") != SCHEMA or not isinstance(questions.get("questions"), list) or not questions["questions"]:
        raise KnowledgeError("Invalid benchmark fixture")
    results = []
    for q in questions["questions"]:
        if not isinstance(q, dict) or not isinstance(q.get("query"), str) or not isinstance(q.get("expected_paths"), list) or not q["expected_paths"]:
            raise KnowledgeError("Invalid benchmark question")
        hits = search(stage_dir, q["query"], k)["hits"]
        rank = next((i + 1 for i, h in enumerate(hits) if h["path"] in q["expected_paths"]), None)
        results.append({"id": q.get("id"), "query": q["query"], "expected_paths": q["expected_paths"], "rank": rank, "top_paths": [h["path"] for h in hits]})
    found = sum(r["rank"] is not None for r in results)
    mrr = sum(1 / r["rank"] if r["rank"] else 0 for r in results) / len(results)
    return {"schema": SCHEMA, "method": "transparent_lexical_baseline", "top_k": k, "question_count": len(results), "hit_at_k": found / len(results), "mrr_at_k": mrr, "details": results, "conclusion": "RETRIEVAL_ONLY_NOT_EVIDENCE"}
