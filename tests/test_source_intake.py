"""No retrieved source or self-declared license may become helmet evidence."""
import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from neuroshield.source_intake import review

ROOT = Path(__file__).resolve().parents[1]


class SourceIntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        directory = self.root / "knowledge" / "corpora"
        directory.mkdir(parents=True)
        for p in (ROOT / "knowledge" / "corpora").glob("*.json"):
            shutil.copyfile(p, directory / p.name)
        shutil.copyfile(ROOT / "knowledge" / "registry.json", self.root / "knowledge" / "registry.json")
        self.file = directory / "intake-ledger.json"

    def edit(self, change):
        data = json.loads(self.file.read_text(encoding="utf-8"))
        change(data)
        self.file.write_text(json.dumps(data), encoding="utf-8")

    def test_all_leads_remain_s0_and_blocked(self):
        result = review(self.root)
        self.assertEqual(result["status"], "BLOCKED_EXTERNAL_QUALIFICATION")
        self.assertEqual(result["scientific_evidence_level"], "S0")
        self.assertEqual(result["source_count"], 3)
        self.assertTrue(all(not s["data_import_authorized"] for s in result["sources"]))

    def test_ledger_and_catalog_hashes_are_stable_and_change_with_metadata(self):
        before = review(self.root)
        self.assertEqual(before["ledger_identity_sha256"], review(self.root)["ledger_identity_sha256"])
        self.assertEqual(len(before["ledger_identity_sha256"]), 64)
        self.assertEqual(len(before["biomechanics_catalog_identity_sha256"]), 64)
        self.assertEqual(len(before["sources"][0]["source_version"]) > 0, True)
        self.edit(lambda a: a["sources"][0].update(limits=a["sources"][0]["limits"] + " Review pending."))
        after = review(self.root)
        self.assertNotEqual(before["ledger_identity_sha256"], after["ledger_identity_sha256"])
        self.assertEqual(before["biomechanics_catalog_identity_sha256"], after["biomechanics_catalog_identity_sha256"])

    def test_restricted_and_publication_blockers(self):
        results = {r["source_id"]: r for r in review(self.root)["sources"]}
        self.assertIn("SOURCE_FILES_RESTRICTED", results["zenodo-hockey-imu-2026"]["blockers"])
        self.assertIn("NO_RAW_MEASUREMENT_DATASET", results["vt-cranium-resonance-index-2026"]["blockers"])
        self.assertIn("FILE_SHA256_VERIFIED_MISSING", results["borealis-escooter-headneck-2024"]["blockers"])

    def test_reject_research_evidence_escalation(self):
        self.edit(lambda a: a["sources"][0].update(scientific_evidence_level="S2"))
        with self.assertRaisesRegex(ValueError, "Unexpected intake fields"):
            review(self.root)

    def test_reject_raw_content_and_local_paths(self):
        for key in ("raw_data", "local_path", "download_url", "license_approved"):
            with self.subTest(key=key):
                shutil.copyfile(ROOT/"knowledge"/"corpora"/"intake-ledger.json", self.file)
                self.edit(lambda a: a["sources"][0].update({key: "secret or unreviewed file"}))
                with self.assertRaises(ValueError):
                    review(self.root)

    def test_reject_unknown_or_duplicate_source(self):
        self.edit(lambda a: a["sources"][0].update(source_id="unreviewed-source"))
        with self.assertRaises(ValueError):
            review(self.root)
        shutil.copyfile(ROOT/"knowledge"/"corpora"/"intake-ledger.json", self.file)
        self.edit(lambda a: a["sources"].append(copy.deepcopy(a["sources"][0])))
        with self.assertRaises(ValueError):
            review(self.root)

    def test_unreviewed_flags_must_be_booleans(self):
        self.edit(lambda a: a["sources"][0].update(file_license_reviewed=1))
        with self.assertRaisesRegex(ValueError, "booleans"):
            review(self.root)

    def test_self_attested_reviews_never_promote_or_import(self):
        self.edit(lambda a: [a["sources"][0].update({flag: True}) for flag in (
            "file_license_reviewed", "permission_to_analyze_verified",
            "file_sha256_verified", "calibration_reviewed",
            "coordinate_frames_verified", "signal_units_verified", "independent_lab_reviewed")])
        result = review(self.root)["sources"][0]
        self.assertEqual(result["status"], "REVIEW_REQUIRED")
        self.assertEqual(result["scientific_evidence_level"], "S0")
        self.assertFalse(result["data_import_authorized"])

    def test_symlinked_ledger_rejected(self):
        self.file.unlink()
        try:
            self.file.symlink_to(ROOT/"knowledge"/"corpora"/"intake-ledger.json")
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks unavailable")
        with self.assertRaises(ValueError):
            review(self.root)

    def test_duplicate_json_keys_rejected(self):
        self.file.write_text('{"schema":"neuroshield.intake-ledger.v1","schema":"other","sources":[]}')
        with self.assertRaisesRegex(ValueError, "Duplicate JSON field"):
            review(self.root)


if __name__ == "__main__":
    unittest.main()
