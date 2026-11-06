"""Negative and positive gates for a metadata-only external EEG catalog."""
from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from neuroshield import ecosystem

ROOT = Path(__file__).resolve().parents[1]


class EcosystemCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "knowledge" / "ecosystem" / "projects.json"
        self.path.parent.mkdir(parents=True)
        self.obj = ecosystem.load_catalog(ROOT)
        self._write()

    def _write(self):
        self.path.write_text(json.dumps(self.obj, indent=2) + "\n", encoding="utf-8")

    def assert_invalid(self):
        with self.assertRaises(ecosystem.EcosystemError):
            ecosystem.load_catalog(self.root)

    def test_real_catalog_is_non_authoritative_and_reproducible(self):
        report = ecosystem.audit(ROOT)
        self.assertGreaterEqual(report["project_count"], 20)
        self.assertFalse(report["license_reuse_authorized"])
        self.assertFalse(report["external_evidence_validated"])
        self.assertFalse(report["network_checks_performed"])
        self.assertEqual(report["status"], "PASS_STRUCTURE_ONLY")

    def test_category_and_search_are_deterministic(self):
        cats = ecosystem.find(ROOT, category="headwear")
        self.assertTrue(cats)
        self.assertTrue(all(x["category"] == "headwear" for x in cats))
        results = ecosystem.find(ROOT, query="electrode headset")
        self.assertEqual(results, ecosystem.find(ROOT, query="electrode headset"))
        self.assertTrue(any(x["id"] == "ultracortex-mark-iv" for x in results))
        self.assertEqual(ecosystem.find(ROOT, project_id="brainflow-interface")[0]["title"],
                         "BrainFlow biosensor interface")

    def test_reject_duplicate_identifiers_and_links(self):
        self.obj["entries"][1]["id"] = self.obj["entries"][0]["id"]
        self._write()
        self.assert_invalid()
        self.obj = ecosystem.load_catalog(ROOT)
        self.obj["entries"][1]["url"] = self.obj["entries"][0]["url"]
        self._write()
        self.assert_invalid()

    def test_reject_non_https_private_or_unauthorized_claim(self):
        self.obj["entries"][0]["url"] = "http://untrusted.example.net/project"
        self._write()
        self.assert_invalid()
        self.obj = ecosystem.load_catalog(ROOT)
        self.obj["entries"][0]["url"] = "https://token:secret@example.com/resource"
        self._write()
        self.assert_invalid()
        self.obj = ecosystem.load_catalog(ROOT)
        self.obj["entries"][0]["reuse_authorized"] = True
        self._write()
        self.assert_invalid()
        self.obj = ecosystem.load_catalog(ROOT)
        self.obj["entries"][0]["license_review"] = "approved"
        self._write()
        self.assert_invalid()

    def test_reject_unexpected_raw_data_and_unknown_evidence_status(self):
        self.obj["entries"][0]["recording_data"] = "private EEG samples"
        self._write()
        self.assert_invalid()
        self.obj = ecosystem.load_catalog(ROOT)
        self.obj["entries"][0]["evidence_role"] = "validated"
        self._write()
        self.assert_invalid()

    def test_reject_duplicate_json_property(self):
        raw = self.path.read_text("utf-8")
        self.path.write_text(raw.replace('"schema":', '"schema": "forged", "schema":', 1))
        self.assert_invalid()

    def test_reject_symlink_catalog(self):
        other = self.root / "catalog-backup.json"
        other.write_bytes(self.path.read_bytes())
        self.path.unlink()
        try:
            self.path.symlink_to(other)
        except (NotImplementedError, OSError):
            self.skipTest("Platform does not permit creating symlinks")
        self.assert_invalid()

    def test_query_safety_and_missing_project(self):
        with self.assertRaises(ecosystem.EcosystemError):
            ecosystem.find(ROOT, query=" ")
        with self.assertRaises(ecosystem.EcosystemError):
            ecosystem.find(ROOT, category="private_subjects")
        with self.assertRaises(ecosystem.EcosystemError):
            ecosystem.find(ROOT, project_id="unknown")
        self.assertEqual(ecosystem.find(ROOT, query="zzzznoresultszzzz"), [])

    def test_cli_audit_with_read_only_root(self):
        output = StringIO()
        with redirect_stdout(output):
            code = ecosystem.main(["audit", "--root", str(ROOT)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())["authority"],
                         "REFERENCE_ONLY_NO_REUSE_PERMISSION")


if __name__ == "__main__":
    unittest.main()
