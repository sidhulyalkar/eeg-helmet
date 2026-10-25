"""Smoke-test the public synthetic repeatability CLI end-to-end."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from neuroshield.replicate_study import evaluate_study

ROOT = Path(__file__).resolve().parents[1]


class ReplicateDemoCLITests(unittest.TestCase):
    def test_generator_to_evaluator_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as workspace:
            folder = Path(workspace) / "synthetic-studies"
            generate = [sys.executable, str(ROOT / "scripts" / "make_replicate_demo.py"), str(folder)]
            subprocess.run(generate, check=True, capture_output=True, text=True)
            study = folder / "study-SYNTHETIC.json"
            report = evaluate_study(study)
            self.assertEqual(report["pair_count"], 3)
            self.assertEqual(report["scientific_evidence_level"], "S0")
            self.assertEqual(report["screen"], "REGRESSIONS_FLAGGED")
            self.assertEqual(json.loads(study.read_text())["scope"], "NONHUMAN_PAIRED_IMPACT_TRIALS")
            rerun = subprocess.run(generate, capture_output=True, text=True)
            self.assertNotEqual(rerun.returncode, 0, "Generator must not overwrite existing trials")
            self.assertEqual(report, evaluate_study(study))


if __name__ == "__main__":
    unittest.main()
