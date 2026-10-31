"""Regression tests for independent reproduction exercise semantics (S0 only)."""
import json
import tempfile
import unittest
from pathlib import Path

from neuroshield.agent_protocol import validate_request
from neuroshield.reproduction_challenge import (
    CASES, REPORT_NAME, PASS_STATUSES, run_challenge, verify_challenge,
)


def faux_runner(task, dest):
    dest.mkdir()
    (dest / "task.json").write_text(json.dumps(validate_request(task)))
    # Fixed test receipts; a real CLI uses the installed scientific kernel.
    return {"task_sha256": task["task_id"], "result_sha256": task["operation"]}


def faux_replay(path):
    task = json.loads((path / "task.json").read_text())
    return {"status": "REPRODUCED_EXACT", "task_sha256": task["task_id"],
            "recorded_result_sha256": task["operation"]}


class ExerciseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name) / "challenge"

    def run_fake(self):
        return run_challenge(self.directory, bundle_runner=faux_runner, replay_runner=faux_replay)

    def verify_fake(self):
        return verify_challenge(self.directory, replay_runner=faux_replay)

    def test_both_cases_replay_and_no_independence_claim(self):
        report = self.run_fake()
        self.assertEqual(report["status"], "PASS_COMPUTATIONAL_ONLY")
        self.assertEqual([x["case_id"] for x in report["cases"]], ["impact", "numerics"])
        self.assertEqual(report["scientific_evidence_level"], "S0")
        self.assertEqual(report["independent_human_reproduction"], "NOT_ESTABLISHED")
        verified = self.verify_fake()
        self.assertEqual(verified["status"], "PASS_COMPUTATIONAL_ONLY")
        self.assertNotIn("hostname", str(report))
        self.assertTrue((self.directory / REPORT_NAME).is_file())

    def test_second_case_executes_after_first_fails(self):
        calls = []
        def failing_runner(task, path):
            calls.append(task["task_id"])
            if task["task_id"] == "repro-impact":
                raise ValueError("secret /home/someone/private.csv")
            return faux_runner(task, path)
        report = run_challenge(self.directory, bundle_runner=failing_runner, replay_runner=faux_replay)
        self.assertEqual(calls, ["repro-impact", "repro-numerics"])
        self.assertEqual(report["status"], "FAILURES_RETAINED")
        self.assertEqual(report["cases"][0]["error_code"], "CASE_INVALID_ARTIFACT")
        self.assertNotIn("private.csv", (self.directory / REPORT_NAME).read_text())
        self.assertEqual(self.verify_fake()["status"], "NOT_REPRODUCED")

    def test_replay_failure_is_not_silently_accepted(self):
        def altered(path):
            out = faux_replay(path)
            out["status"] = "FAILED_REPRODUCTION_MISMATCH"
            return out
        report = run_challenge(self.directory, bundle_runner=faux_runner, replay_runner=altered)
        self.assertEqual(report["status"], "FAILURES_RETAINED")
        self.assertTrue(all(x["error_code"] == "REPLAY_NOT_REPRODUCED" for x in report["cases"]))

    def test_cannot_overwrite_existing_exercise(self):
        self.run_fake()
        with self.assertRaises(FileExistsError):
            self.run_fake()

    def test_cannot_tamper_evidence_level(self):
        self.run_fake()
        p = self.directory / REPORT_NAME
        obj = json.loads(p.read_text())
        obj["scientific_evidence_level"] = "S3"
        p.write_text(json.dumps(obj))
        with self.assertRaisesRegex(ValueError, "escalation"):
            self.verify_fake()

    def test_cannot_forge_human_independence(self):
        self.run_fake()
        p = self.directory / REPORT_NAME
        obj = json.loads(p.read_text())
        obj["independent_human_reproduction"] = "VERIFIED_BY_AUTHOR"
        p.write_text(json.dumps(obj))
        with self.assertRaisesRegex(ValueError, "escalation"):
            self.verify_fake()

    def test_duplicate_or_missing_cases_are_not_accepted(self):
        self.run_fake()
        p = self.directory / REPORT_NAME
        obj = json.loads(p.read_text())
        obj["cases"] = [obj["cases"][0], obj["cases"][0]]
        p.write_text(json.dumps(obj))
        with self.assertRaisesRegex(ValueError, "identity"):
            self.verify_fake()

    def test_forged_result_identity_is_caught_by_replay(self):
        self.run_fake()
        p = self.directory / REPORT_NAME
        obj = json.loads(p.read_text())
        obj["cases"][0]["result_sha256"] = "0" * 64
        p.write_text(json.dumps(obj))
        res = self.verify_fake()
        self.assertEqual(res["status"], "NOT_REPRODUCED")
        self.assertEqual(res["cases"][0]["status"], "FAILED_REPLAY_MISMATCH")

    def test_different_valid_scenario_cannot_replace_frozen_task(self):
        self.run_fake()
        path = self.directory / "impact" / "task.json"
        obj = json.loads(path.read_text())
        obj["inputs"]["scenario"] = "facemask"
        path.write_text(json.dumps(obj))
        # A consistent but different valid task is not the agreed reproduction test.
        self.assertEqual(self.verify_fake()["cases"][0]["status"], "FAILED_TASK_CONTRACT")

    def test_case_bundle_mutation_detected_by_replay(self):
        self.run_fake()
        path = self.directory / "impact" / "task.json"
        obj = json.loads(path.read_text())
        obj["operation"] = "audit_synthetic_numerics"
        path.write_text(json.dumps(obj))
        res = self.verify_fake()
        self.assertEqual(res["status"], "NOT_REPRODUCED")

    def test_fail_if_extra_unknown_file_in_output(self):
        self.run_fake()
        (self.directory / "user-data.csv").write_text("secret")
        with self.assertRaisesRegex(ValueError, "Unexpected files"):
            self.verify_fake()

    def test_broken_symlink_case_cannot_pass(self):
        self.run_fake()
        import shutil
        shutil.rmtree(self.directory / "impact")
        (self.directory / "impact").symlink_to(self.directory / "numerics", target_is_directory=True)
        self.assertEqual(self.verify_fake()["status"], "NOT_REPRODUCED")

    def test_can_repeat_verify_without_writing(self):
        self.run_fake()
        before=(self.directory / REPORT_NAME).read_bytes()
        a=self.verify_fake();b=self.verify_fake()
        self.assertEqual(a,b)
        self.assertEqual(before,(self.directory / REPORT_NAME).read_bytes())

    def test_real_installed_kernels_smoke(self):
        """Full CI executes real scientific kernels in addition to unit fake runner."""
        from neuroshield.agent_protocol import create_bundle
        from neuroshield.reproduction import replay_bundle
        report=run_challenge(self.directory,bundle_runner=create_bundle,replay_runner=replay_bundle)
        self.assertEqual(report["status"],"PASS_COMPUTATIONAL_ONLY")
        self.assertEqual(verify_challenge(self.directory)["status"],"PASS_COMPUTATIONAL_ONLY")
        self.assertTrue(all(x["replay_status"] in PASS_STATUSES for x in report["cases"]))


if __name__ == "__main__":
    unittest.main()
