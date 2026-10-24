"""Privacy, provenance, and navigation contracts for the optional retrieval layer."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from neuroshield.knowledge import KnowledgeError, audit, benchmark, committed_sources, search, stage, _safe_path


class KnowledgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project = Path(__file__).resolve().parents[1]

    def _git(self, root, *args):
        subprocess.run(["git", "-C", str(root), *args], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def _repo(self):
        workspace = tempfile.TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        root = Path(workspace.name) / "repo"
        root.mkdir()
        (root / "src/neuroshield").mkdir(parents=True)
        (root / "tests").mkdir()
        (root / "knowledge").mkdir()
        (root / "docs").mkdir()
        (root / "data").mkdir()
        (root / "README.md").write_text("Synthetic helmet simulation with no clinical authority\n")
        (root / "src/neuroshield/physics.py").write_text("def simulate_impact():\n    return 'synthetic'\n")
        (root / "tests/test_physics.py").write_text("def test_simulate_impact(): pass\n")
        (root / "docs/research-contract.md").write_text("S0 only: no concussion prediction or measured protective claims\n")
        (root / "knowledge/registry.json").write_text(json.dumps({
            "schema": "neuroshield.knowledge.v1",
            "sources": [{"id": "physics", "kind": "code", "path": "src/neuroshield/physics.py"}],
            "claims": [{"id": "claim", "kind": "model_assumption", "statement": "Only synthetic impact simulation is implemented.",
                        "source_ids": ["physics"], "evidence_tier": "S0", "inference_scope": "synthetic_research_only",
                        "limitations": "No physical calibration and no clinical basis."}]
        }))
        (root / "knowledge/questions.json").write_text(json.dumps({
            "schema": "neuroshield.knowledge.v1", "questions": [
                {"id": "Q0", "query": "simulate_impact synthetic", "expected_paths": ["src/neuroshield/physics.py"]}
            ]
        }))
        self._git(root, "init", "-q")
        self._git(root, "config", "user.name", "Test")
        self._git(root, "config", "user.email", "test@example.invalid")
        self._git(root, "add", "README.md", "src", "tests", "knowledge", "docs")
        self._git(root, "commit", "-qm", "Initial committed sources")
        return root

    def test_project_registry_passes_at_s0(self):
        result = audit(self.project)
        self.assertEqual(result["status"], "PASS_REGISTRY_STRUCTURE_ONLY")
        self.assertEqual(result["max_evidence_tier"], "S0")
        self.assertFalse(result["clinical_authority"])

    def test_rejects_unsafe_paths(self):
        for bad in ("../secret.md", "data/private.md", "examples/subjects.json", ".env", "src/neuroshield/../../secret.py", "/tmp/out.py", "src/neuroshield/.hidden.py", "src/neuroshield/web/app.js", "docs/report.pdf"):
            with self.subTest(path=bad):
                self.assertFalse(_safe_path(bad))

    def test_staging_omits_untracked_and_worktree_modifications(self):
        root = self._repo()
        (root / "src/neuroshield/physics.py").write_text("UNCOMMITTED_SECRET\n")
        (root / "data/patient-EEG.csv").write_text("PRIVATE HUMAN SIGNAL\n")
        (root / "docs/untracked.md").write_text("PRIVATE UNTRACKED NOTE\n")
        destination = root.parent / "safe-stage"
        outcome = stage(root, destination)
        text = (destination / "src/neuroshield/physics.py").read_text()
        self.assertIn("simulate_impact", text)
        self.assertNotIn("UNCOMMITTED_SECRET", text)
        self.assertFalse((destination / "docs/untracked.md").exists())
        self.assertFalse((destination / "data").exists())
        self.assertIn("STAGED_COMMITTED", outcome["status"])
        self.assertFalse((destination / "knowledge/questions.json").exists())
        self.assertFalse((destination / "knowledge/registry.json").exists())
        self.assertEqual(outcome["files"], len(list(destination.rglob("*"))) - len(list(p for p in destination.rglob("*") if p.is_dir())) - 1)

    def test_manifest_integrity_search_and_benchmark(self):
        root = self._repo()
        destination = root.parent / "safe-stage"
        stage(root, destination)
        hit = search(destination, "simulate_impact synthetic", 3)
        self.assertEqual(hit["hits"][0]["path"], "src/neuroshield/physics.py")
        self.assertEqual(hit["hits"][0]["line"], 1)
        self.assertEqual(benchmark(root, destination)["hit_at_k"], 1)
        with (destination / "src/neuroshield/physics.py").open("a") as stream:
            stream.write("NEW CONTENT")
        with self.assertRaises(KnowledgeError):
            search(destination, "simulate", 2)

    def test_stage_never_overwrites_or_stages_inside_checkout(self):
        root = self._repo()
        with self.assertRaises(KnowledgeError):
            stage(root, root / "new-staging")
        outside = root.parent / "outside"
        stage(root, outside)
        with self.assertRaises(KnowledgeError):
            stage(root, outside)

    def test_rejects_evidence_promotion_and_unresolved_source(self):
        root = self._repo()
        p = root / "knowledge/registry.json"
        registry = json.loads(p.read_text())
        registry["claims"][0]["evidence_tier"] = "S4"
        p.write_text(json.dumps(registry))
        with self.assertRaises(KnowledgeError):
            audit(root)
        registry["claims"][0]["evidence_tier"] = "S0"
        registry["claims"][0]["source_ids"] = ["unknown"]
        p.write_text(json.dumps(registry))
        with self.assertRaises(KnowledgeError):
            audit(root)

    def test_symlink_not_imported(self):
        root = self._repo()
        target = root.parent / "secret.md"
        target.write_text("SECRET")
        symlink = root / "docs" / "external.md"
        try:
            symlink.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("OS does not allow symlink creation")
        self._git(root, "add", "docs/external.md")
        self._git(root, "commit", "-qm", "Add dangerous symlink")
        with self.assertRaises(KnowledgeError):
            committed_sources(root)


if __name__ == "__main__":
    unittest.main()
