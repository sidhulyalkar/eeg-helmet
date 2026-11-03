"""Unpaired nonhuman observational experiments must preserve missing cells and failures."""
import copy
import hashlib
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from neuroshield.unpaired_design import evaluate_design, read_plan, validate_plan, main


def fixture():
    trials = []
    for i, (stratum, level, angle) in enumerate([
        ("curb-0", "helmeted", 0), ("curb-0", "unhelmeted", 0),
        ("curb-0", "unhelmeted", 0), ("curb-55", "helmeted", 55),
        ("curb-55", "helmeted", 55), ("curb-55", "unhelmeted", 55)], 1):
        trials.append({
            "trial_id": f"trial-{i:02d}", "acquisition_id": f"acquisition-{i:02d}",
            "raw_sha256": None, "run_order": i, "record_status": "METADATA_ONLY",
            "record_reason": "SOURCE_NOT_ACQUIRED",
            "factor_level": level, "stratum_id": stratum,
            "impact_angle_deg": angle, "impact_speed_m_s": None,
            "rig_id": "rig-synthetic", "headform_id": "headform-synthetic",
            "helmet_unit_id": f"helmet-{i:02d}" if level == "helmeted" else None,
            "test_day_id": f"day-{(i+1)//2}",
        })
    return {
        "schema_version": "neuroshield.unpaired-design/0.1",
        "study_id": "fictional-six-conditions",
        "question": "How could angle and helmet presence be confounded in a fictional set of nonhuman curb-impact trials?",
        "origin": "SYNTHETIC_HEADFORM_FIXTURE",
        "analysis_unit": "physical_impact_trial",
        "comparison_factor": "helmet_presence",
        "comparison_levels": ["unhelmeted", "helmeted"],
        "stratification_factor": "curb_angle",
        "strata": ["curb-0", "curb-55"],
        "planned_trial_count": 6,
        "preregistration_digest_sha256": "b" * 64,
        "preregistration_status": "AUTHOR_DECLARED_TIMESTAMP_UNVERIFIED",
        "assignment_status": "NOT_RECORDED",
        "nominal_speed_m_s": 5.56,
        "speed_tolerance_m_s": 0.5,
        "angle_tolerance_deg": 0.5,
        "primary_outcome": "head_peak_linear_acceleration_m_s2",
        "secondary_outcomes": ["head_peak_angular_acceleration_rad_s2", "upper_neck_peak_force_n"],
        "trials": trials,
    }


class UnpairedDesignTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "unpaired.json"
        self.plan = fixture()
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.plan), encoding="utf-8")

    def test_empty_raw_metadata_fixture_preserves_s0(self):
        r = evaluate_design(self.plan)
        self.assertEqual(r["status"], "FACTORIAL_DESIGN_REVIEW_ONLY")
        self.assertEqual(r["scientific_evidence_level"], "S0")
        self.assertEqual(r["planned_trial_count"], 6)
        self.assertEqual(r["recorded_trial_count"], 0)
        self.assertEqual([x["total_declared_trials"] for x in r["strata"]], [3, 3])
        self.assertIn("UNACQUIRED_RAW_MEASUREMENTS", r["warnings"])
        self.assertFalse(r["statistical_tests_performed"])
        self.assertFalse(r["causal_effect_authorized"])
        self.assertFalse(r["data_import_authorized"])

    def test_record_statuses_are_preserved(self):
        self.plan["trials"][0].update(record_status="FAILED", record_reason="SENSOR_FAILURE")
        self.plan["trials"][1].update(record_status="EXCLUDED", record_reason="POSTHOC_EXCLUSION")
        r = evaluate_design(self.plan)
        cell_h = r["strata"][0]["cells"][1]
        cell_u = r["strata"][0]["cells"][0]
        self.assertEqual(cell_h["record_status_counts"]["FAILED"], 1)
        self.assertEqual(cell_u["record_status_counts"]["EXCLUDED"], 1)
        self.assertIn("FAILURES_OR_EXCLUSIONS_PRESERVED", r["warnings"])
        self.assertIn("EXCLUSION_MAY_BIAS_ANALYSIS", r["warnings"])

    def test_recognizes_separate_strata_and_does_not_pool(self):
        r = evaluate_design(self.plan)
        self.assertEqual(r["stratification_factor"], "curb_angle")
        self.assertEqual(len(r["strata"]), 2)
        self.assertIn("NO_CROSS_STRATUM_POOLING_WITHOUT_NEW_PROTOCOL", r["warnings"])
        self.assertTrue(all(x["descriptive_two_level_coverage_only"] for x in r["strata"]))
        self.assertTrue(all(not x["effect_estimation_authorized"] for x in r["strata"]))

    def test_order_confound_flag(self):
        p = fixture()
        p["strata"] = ["curb-0"]
        p["trials"] = p["trials"][:3]
        p["planned_trial_count"] = 3
        # Order: unhelmeted first and second, helmeted last.
        p["trials"][0]["run_order"] = 3
        p["trials"][1]["run_order"] = 1
        p["trials"][2]["run_order"] = 2
        r = evaluate_design(p)
        self.assertIn("FACTOR_CONFOUNDED_WITH_SEQUENTIAL_TEST_ORDER", r["warnings"])

    def test_empty_factor_cell_is_reported_not_imputed(self):
        self.plan["trials"][0]["factor_level"] = "unhelmeted"
        r = evaluate_design(self.plan)
        self.assertIn("EMPTY_FACTOR_CELL", r["warnings"])
        self.assertIn("NO_WITHIN_STRATUM_TWO_LEVEL_COMPARISON", r["warnings"])

    def test_duplicate_raw_hash_rejected_for_recorded_trials(self):
        digest = hashlib.sha256(b"fictional").hexdigest()
        for trial in self.plan["trials"][:2]:
            trial.update(record_status="RECORDED", record_reason="NONE", raw_sha256=digest)
        with self.assertRaisesRegex(ValueError, "Repeated raw"):
            validate_plan(self.plan)

    def test_recorded_requires_sha(self):
        self.plan["trials"][0].update(record_status="RECORDED", record_reason="NONE")
        with self.assertRaisesRegex(ValueError, "Recorded trials"):
            validate_plan(self.plan)

    def test_metadata_only_forbids_sha(self):
        self.plan["trials"][0]["raw_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "Metadata-only"):
            validate_plan(self.plan)

    def test_completed_recoded_counts_do_not_confer_inference(self):
        for i, trial in enumerate(self.plan["trials"]):
            trial.update(record_status="RECORDED", record_reason="NONE",
                         raw_sha256=hashlib.sha256(str(i).encode()).hexdigest())
        report = evaluate_design(self.plan)
        self.assertEqual(report["recorded_trial_count"], 6)
        self.assertFalse(report["randomization_verified"])
        self.assertFalse(report["independent_samples_inferred"])
        self.assertFalse(report["calibration_verified"])

    def test_reject_hidden_failed_trial(self):
        self.plan["trials"] = self.plan["trials"][:-1]
        with self.assertRaisesRegex(ValueError, "Every planned trial"):
            validate_plan(self.plan)

    def test_reject_duplicate_ids(self):
        for name in ("trial_id", "acquisition_id", "run_order"):
            with self.subTest(name=name):
                p = fixture()
                p["trials"][1][name] = p["trials"][0][name]
                with self.assertRaises(ValueError):
                    validate_plan(p)

    def test_reject_invalid_status_reason(self):
        self.plan["trials"][0]["record_status"] = "FAILED"
        with self.assertRaisesRegex(ValueError, "reason"):
            validate_plan(self.plan)

    def test_reject_human_origin(self):
        self.plan["origin"] = "HUMAN_EEG"
        with self.assertRaisesRegex(ValueError, "nonhuman"):
            validate_plan(self.plan)

    def test_reject_pseudoreplicated_samples(self):
        self.plan["analysis_unit"] = "sensor_samples"
        with self.assertRaisesRegex(ValueError, "impact trials"):
            validate_plan(self.plan)

    def test_reject_p_value_or_evidence_escalation_fields(self):
        for key in ("p_value", "clinical_risk", "evidence_tier", "authorization"):
            with self.subTest(key=key):
                p = fixture()
                p[key] = 0.0001
                with self.assertRaisesRegex(ValueError, "exactly"):
                    validate_plan(p)

    def test_reject_conflicting_angles_within_stratum(self):
        self.plan["trials"][1]["impact_angle_deg"] = 55
        with self.assertRaisesRegex(ValueError, "Incompatible"):
            validate_plan(self.plan)

    def test_reject_speed_violation(self):
        self.plan["trials"][0]["impact_speed_m_s"] = 7
        with self.assertRaisesRegex(ValueError, "speed"):
            validate_plan(self.plan)

    def test_reject_boolean_in_numeric_field(self):
        self.plan["trials"][0]["run_order"] = True
        with self.assertRaises(ValueError):
            validate_plan(self.plan)

    def test_reject_nonfinite_numeric(self):
        self.plan["trials"][0]["impact_angle_deg"] = float("nan")
        with self.assertRaises(ValueError):
            validate_plan(self.plan)

    def test_reject_unverified_randomized_assertion(self):
        self.plan["assignment_status"] = "RANDOMIZED_CONFIRMED"
        with self.assertRaisesRegex(ValueError, "unverified"):
            validate_plan(self.plan)

    def test_reject_invalid_outcome(self):
        self.plan["primary_outcome"] = "predicted_concussion_risk"
        with self.assertRaisesRegex(ValueError, "physical quantity"):
            validate_plan(self.plan)

    def test_reject_unknown_level(self):
        self.plan["trials"][0]["factor_level"] = "different"
        with self.assertRaises(ValueError):
            validate_plan(self.plan)

    def test_duplicate_json_keys_refused(self):
        self.path.write_text('{"schema_version":"neuroshield.unpaired-design/0.1",'
                             '"schema_version":"forged"}')
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            read_plan(self.path)

    def test_symlinked_plan_refused(self):
        alias = self.root / "link.json"
        try:
            alias.symlink_to(self.path)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks not available")
        with self.assertRaisesRegex(ValueError, "symlinked"):
            read_plan(alias)

    def test_cli_no_overwrite(self):
        target = self.root / "report.json"
        target.write_text("KEEP")
        with redirect_stdout(StringIO()), self.assertRaises(SystemExit) as result:
            main([str(self.path), "--out", str(target)])
        self.assertEqual(result.exception.code, 2)
        self.assertEqual(target.read_text(), "KEEP")

    def test_cli_no_raw_ids_export(self):
        target = self.root / "report.json"
        with redirect_stdout(StringIO()):
            self.assertEqual(main([str(self.path), "--out", str(target)]), 0)
        report = json.loads(target.read_text())
        encoded = json.dumps(report)
        self.assertEqual(report["scientific_evidence_level"], "S0")
        self.assertNotIn("acquisition-01", encoded)
        self.assertNotIn("trial-01", encoded)
        self.assertNotIn("raw_sha256", encoded)


if __name__ == "__main__":
    unittest.main()
