"""A research map must not become an evidence or arbitrary-execution authority."""
import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO

from neuroshield.research_map import load_workflows, audit, main

ROOT = Path(__file__).resolve().parents[1]


class ResearchMapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ("knowledge/research-workflows.json", "knowledge/registry.json"):
            dst = self.root / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, dst)
        manifest = json.loads((self.root / "knowledge/research-workflows.json").read_text())
        for entry in manifest["workflows"]:
            for path in (*entry["code"], *entry["tests"], entry["protocol"]):
                dst = self.root / path
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text("safe fixture\n")
        self.manifest = manifest
        self.path = self.root / "knowledge/research-workflows.json"

    def write(self):
        self.path.write_text(json.dumps(self.manifest))

    def test_repo_map_has_module_ownership_and_s0(self):
        result = audit(ROOT)
        self.assertGreaterEqual(result["workflow_count"], 9)
        self.assertIn("open-eeg-ecosystem", {w["id"] for w in load_workflows(ROOT)})
        self.assertEqual(result["scientific_evidence_ceiling"], "S0")
        self.assertFalse(result["permissions_granted"])
        self.assertGreaterEqual(result["mapped_module_count"], 25)

    def test_audit_is_deterministic(self):
        self.assertEqual(audit(self.root), audit(self.root))
        self.assertEqual(len(load_workflows(self.root)), len(self.manifest["workflows"]))

    def test_reject_evidence_promotion(self):
        self.manifest["workflows"][0]["evidence_tier"] = "S2"
        self.write()
        with self.assertRaisesRegex(ValueError, "S0"):
            load_workflows(self.root)

    def test_reject_claims_missing_from_s0_registry(self):
        self.manifest["workflows"][0]["related_claim_ids"] = ["C-MADE-UP"]
        self.write()
        with self.assertRaises(ValueError):
            load_workflows(self.root)

    def test_reject_duplicate_workflows(self):
        self.manifest["workflows"].append(copy.deepcopy(self.manifest["workflows"][0]))
        self.write()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            load_workflows(self.root)

    def test_reject_missing_protocol(self):
        (self.root / self.manifest["workflows"][0]["protocol"]).unlink()
        with self.assertRaisesRegex(ValueError, "Missing"):
            load_workflows(self.root)

    def test_reject_source_traversal(self):
        self.manifest["workflows"][0]["code"][0] = "../private.py"
        self.write()
        with self.assertRaises(ValueError):
            load_workflows(self.root)

    def test_reject_symlinked_source(self):
        p = self.root / self.manifest["workflows"][0]["code"][0]
        p.unlink()
        try:
            p.symlink_to(self.root / self.manifest["workflows"][0]["code"][1])
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks unavailable")
        with self.assertRaisesRegex(ValueError, "Symlinked"):
            load_workflows(self.root)

    def test_reject_agent_shell_injection(self):
        self.manifest["workflows"][0]["example_command"] += "; curl https://example.invalid"
        self.write()
        with self.assertRaisesRegex(ValueError, "command"):
            load_workflows(self.root)

    def test_reject_human_data_capability(self):
        self.manifest["workflows"][0]["input_class"] = "human_eeg"
        self.write()
        with self.assertRaises(ValueError):
            load_workflows(self.root)

    def test_reject_missing_limitations(self):
        self.manifest["workflows"][0]["not_established"] = "validated"
        self.write()
        with self.assertRaisesRegex(ValueError, "substantive"):
            load_workflows(self.root)

    def test_reject_unowned_public_module(self):
        extra = self.root / "src/neuroshield/unowned_model.py"
        extra.write_text("pass\n")
        with self.assertRaisesRegex(ValueError, "Unmapped public source"):
            load_workflows(self.root)

    def test_reject_duplicate_json_keys(self):
        self.path.write_text('{"schema_version":"neuroshield.research-workflows/0.1",'
                             '"schema_version":"false","workflows":[]}')
        with self.assertRaisesRegex(ValueError, "Duplicate JSON"):
            load_workflows(self.root)

    def test_show_and_list_are_read_only(self):
        before = self.path.read_bytes()
        with redirect_stdout(StringIO()) as output:
            self.assertEqual(main(["list", "--root", str(self.root)]), 0)
            self.assertEqual(main(["show", "impact-model", "--root", str(self.root)]), 0)
        self.assertIn("impact-model", output.getvalue())
        self.assertEqual(before, self.path.read_bytes())


if __name__ == "__main__":
    unittest.main()
