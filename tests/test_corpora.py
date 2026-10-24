"""Metadata-only research references must never assert experimental validity."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from neuroshield import corpora
from neuroshield.knowledge import KnowledgeError

ROOT = Path(__file__).resolve().parents[1]


class CorpusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "repo"
        (self.root / "knowledge" / "corpora").mkdir(parents=True)
        for path in (ROOT / "knowledge" / "corpora").glob("*.json"):
            shutil.copyfile(path, self.root / "knowledge" / "corpora" / path.name)
        shutil.copyfile(ROOT / "knowledge" / "registry.json", self.root / "knowledge" / "registry.json")

    def modify(self, domain, transform):
        p = self.root / "knowledge" / "corpora" / f"{domain}.json"
        obj = json.loads(p.read_text())
        transform(obj)
        p.write_text(json.dumps(obj))

    def init_git(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "add", "knowledge"], check=True)
        subprocess.run(["git", "-C", str(self.root), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "Fixture"], check=True)

    def test_audit_all_three(self):
        r = corpora.audit(self.root)
        self.assertEqual(r["corpora"], {"biomechanics": 6, "neural": 3, "evidence": 3})
        self.assertEqual(r["max_evidence_tier"], "S0")
        self.assertFalse(r["physical_validation"])

    def test_source_search_is_reference_navigation_only(self):
        r = corpora.search(self.root, "ND081 pneumatic ram headform", domain="biomechanics")
        self.assertEqual(r["hits"][0]["id"], "nocsae-nd081")
        self.assertEqual(r["hits"][0]["license_status"], "pending_manual_review")
        self.assertEqual(r["authority"], "S0_EXTERNAL_CONTEXT_ONLY")

    def test_benchmark_frozen(self):
        r = corpora.benchmark(self.root)
        self.assertEqual(r["question_count"], 12)
        self.assertEqual(r["method"], "curated_metadata_lexical_v1")
        self.assertGreaterEqual(r["hit_at_k"], .75)
        self.assertNotIn("physical_validation", r)

    def test_duplicate_id_disallowed(self):
        self.modify("neural", lambda x: x["sources"].append(dict(x["sources"][0])))
        with self.assertRaises(KnowledgeError):
            corpora.audit(self.root)

    def test_unreviewed_license_must_not_be_marked_approved(self):
        self.modify("biomechanics", lambda x: x["sources"][0].update(license_status="approved"))
        with self.assertRaises(KnowledgeError):
            corpora.audit(self.root)

    def test_external_import_path_disallowed(self):
        self.modify("biomechanics", lambda x: x["sources"][0].update(local_path="data/private/impact.csv"))
        with self.assertRaises(KnowledgeError):
            corpora.audit(self.root)

    def test_url_must_not_contain_credentials_or_non_https(self):
        for url in ("file:///tmp/example", "https://alice:secret@host.invalid/ref", "http://example.com/ref"):
            with self.subTest(url=url):
                def mutate(x): x["sources"][0]["url"] = url
                self.modify("neural", mutate)
                with self.assertRaises(KnowledgeError):
                    corpora.audit(self.root)
                shutil.copyfile(ROOT / "knowledge" / "corpora" / "neural.json", self.root / "knowledge" / "corpora" / "neural.json")

    def test_evidence_promotion_is_rejected(self):
        self.modify("hypotheses", lambda x: x["hypotheses"][0].update(evidence_tier="S1"))
        with self.assertRaises(KnowledgeError):
            corpora.audit(self.root)

    def test_unknown_claim_link_is_rejected(self):
        self.modify("hypotheses", lambda x: x["hypotheses"][0].update(claim_ids=["made-up-claim"]))
        with self.assertRaises(KnowledgeError):
            corpora.audit(self.root)

    def test_qualification_gap_names_blocker(self):
        r = corpora.qualification_gaps(self.root)
        self.assertEqual(r["status"], "S0_UNVALIDATED")
        self.assertEqual(len(r["hypotheses"]), 4)
        self.assertTrue(all(x["blocking_requirement"] for x in r["hypotheses"]))

    def test_stage_only_committed_metadata_and_checksum(self):
        self.init_git()
        output = Path(self.tmp.name) / "staged"
        r = corpora.stage_metadata(self.root, output)
        self.assertEqual(r["source_count"], 12)
        manifest = json.loads((output / "CORPORA-MANIFEST.json").read_text())
        self.assertEqual(manifest["repository_commit"], r["repository_commit"])
        content = (output / "biomechanics" / "nocsae-nd081.txt").read_text()
        self.assertIn("License pending", content)
        self.assertNotIn("test sample,", content)
        with self.assertRaises(KnowledgeError):
            corpora.stage_metadata(self.root, output)

    def test_windows_crlf_checkout_is_equivalent_to_committed_blob(self):
        self.init_git()
        p = self.root / "knowledge" / "corpora" / "biomechanics.json"
        p.write_bytes(p.read_bytes().replace(b"\n", b"\r\n"))
        output = Path(self.tmp.name) / "crlf-staged"
        result = corpora.stage_metadata(self.root, output)
        self.assertEqual(result["source_count"], 12)

    def test_reject_staging_dirty_catalog(self):
        self.init_git()
        self.modify("biomechanics", lambda x: x["sources"][0].update(relevance="Secret uncommitted data should not be indexed"))
        dest = Path(self.tmp.name) / "dirty"
        with self.assertRaises(KnowledgeError):
            corpora.stage_metadata(self.root, dest)
        self.assertFalse(dest.exists())

    def test_reject_stage_into_repository(self):
        self.init_git()
        with self.assertRaises(KnowledgeError):
            corpora.stage_metadata(self.root, self.root / "data" / "corpus")

    def test_symlink_manifest_disallowed(self):
        p = self.root / "knowledge" / "corpora" / "neural.json"
        p.unlink()
        try:
            p.symlink_to(ROOT / "knowledge" / "corpora" / "neural.json")
        except (OSError, NotImplementedError):
            self.skipTest("OS does not allow symlink creation")
        with self.assertRaises(KnowledgeError):
            corpora.audit(self.root)


if __name__ == "__main__":
    unittest.main()
