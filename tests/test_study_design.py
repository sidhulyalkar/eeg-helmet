"""Adversarial S0-only controls for matched nonhuman experimental design."""
import copy
import hashlib
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from neuroshield.study_design import evaluate_design, main, read_study, validate_study


def fixture():
    blocks = []
    for i in range(4):
        arms = ("reference", "candidate") if i % 2 == 0 else ("candidate", "reference")
        trials = []
        for order, arm in enumerate(arms, 1):
            trials.append({"trial_id": f"trial-{i}-{arm}", "arm": arm, "order": order,
                           "measured_speed_m_s": 5.0 + (0.05 if arm == "candidate" else 0),
                           "helmet_unit_id": f"helmet-{i}-{arm}",
                           "acquisition_id": f"acquisition-{i}-{arm}",
                           "raw_sha256": hashlib.sha256(f"SYNTHETIC-ONLY-{i}-{arm}".encode()).hexdigest()})
        blocks.append({"block_id": f"block-{i}", "stratum_id": "frontal-5ms",
                       "rig_id": "rig-alpha", "headform_id": f"headform-{i//2}",
                       "test_day_id": f"day-{i//2}", "impact_location": "forehead",
                       "impact_angle_deg": 0., "temperature_c": 21., "target_speed_m_s": 5.,
                       "trials": trials})
    return {"schema_version": "neuroshield.study-design/0.1", "study_id": "synthetic-study-01",
            "question": "Under a fixed synthetic frontal impact setup, does the candidate change peak linear acceleration?",
            "origin": "SYNTHETIC_HEADFORM_FIXTURE", "analysis_unit": "matched_impact_block",
            "preregistration_digest_sha256": hashlib.sha256(b"SYNTHETIC PLAN not timestamped").hexdigest(),
            "preregistration_status": "AUTHOR_DECLARED_TIMESTAMP_UNVERIFIED",
            "assignment_policy": "counterbalanced_declared",
            "primary_outcome": "head_peak_linear_acceleration_m_s2",
            "secondary_outcomes": ["head_peak_angular_acceleration_rad_s2", "upper_neck_peak_moment_n_m"],
            "max_speed_deviation_m_s": 0.2, "blocks": blocks}


class StudyDesignTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.plan = fixture()
        self.path = self.root / "study.json"
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.plan), encoding="utf-8")

    def test_evidence_ceiling_and_counterbalanced_order(self):
        r = evaluate_design(self.plan)
        self.assertEqual(r["scientific_evidence_level"], "S0")
        self.assertEqual(r["status"], "DESCRIPTIVE_DESIGN_REVIEW_REQUIRED")
        self.assertEqual(r["block_count"], 4)
        self.assertEqual(r["strata"][0]["first_arm_counts"], {"candidate": 2, "reference": 2})
        self.assertFalse(r["independent_physical_validation"])
        self.assertFalse(r["random_assignment_verified"])
        self.assertFalse(r["preregistration_timing_verified"])
        self.assertFalse(r["data_import_authorized"])
        self.assertIn("SINGLE_RIG_GENERALIZATION_LIMIT", r["warnings"])
        self.assertNotIn("ARM_ORDER_CONFOUNDED", r["warnings"])

    def test_deterministic_and_no_data_or_p_values(self):
        a = evaluate_design(self.plan)
        self.assertEqual(a, evaluate_design(read_study(self.path)))
        self.assertEqual(len(a["study_plan_sha256"]), 64)
        self.assertNotIn("p_value", json.dumps(a))
        self.assertNotIn("SYNTHETIC-ONLY-", json.dumps(a))
        self.assertNotIn("helmet-0", json.dumps(a))

    def test_single_day_and_headform_clusters_are_flagged(self):
        for b in self.plan["blocks"]:
            b["test_day_id"] = "same-day"
            b["headform_id"] = "same-headform"
        r = evaluate_design(self.plan)
        self.assertIn("SINGLE_DAY_CLUSTER", r["warnings"])
        self.assertIn("SINGLE_HEADFORM_CLUSTER", r["warnings"])
        self.assertFalse(r["strata"][0]["independent_samples_inferred"])

    def test_order_confound_and_fixed_order_are_reported(self):
        for b in self.plan["blocks"]:
            for t in b["trials"]:
                t["order"] = 1 if t["arm"] == "reference" else 2
        self.plan["assignment_policy"] = "fixed_order_declared"
        r = evaluate_design(self.plan)
        self.assertIn("ARM_ORDER_CONFOUNDED", r["warnings"])
        self.assertIn("NO_RANDOMIZATION_CLAIM_SUPPORTED", r["warnings"])

    def test_reused_helmet_units_are_clustered(self):
        for b in self.plan["blocks"]:
            for t in b["trials"]:
                t["helmet_unit_id"] = f"shared-{t['arm']}"
        r = evaluate_design(self.plan)
        self.assertIn("HELMET_UNITS_REUSED_CLUSTERED_RESPONSES", r["warnings"])
        self.assertEqual(r["strata"][0]["distinct_helmet_units_per_arm"]["reference"], 1)

    def test_no_cross_stratum_pooling(self):
        for b in self.plan["blocks"][2:]:
            b["stratum_id"] = "oblique-5ms"
            b["impact_angle_deg"] = 55
        r = evaluate_design(self.plan)
        self.assertEqual(r["strata_count"], 2)
        self.assertEqual([x["matched_block_count"] for x in r["strata"]], [2, 2])
        self.assertTrue(all("FEWER_THAN_THREE_MATCHED_BLOCKS" in x["warnings"] for x in r["strata"]))

    def test_reject_pooled_incompatible_angle(self):
        self.plan["blocks"][2]["impact_angle_deg"] = 55
        with self.assertRaisesRegex(ValueError, "Incompatible"):
            validate_study(self.plan)

    def test_reject_unmatched_speed(self):
        self.plan["blocks"][0]["trials"][0]["measured_speed_m_s"] = 5.4
        with self.assertRaisesRegex(ValueError, "speed"):
            validate_study(self.plan)

    def test_reject_repeated_ids_and_raw_hashes(self):
        for key in ("raw_sha256", "acquisition_id", "trial_id"):
            with self.subTest(key=key):
                p = fixture()
                p["blocks"][1]["trials"][0][key] = p["blocks"][0]["trials"][0][key]
                with self.assertRaisesRegex(ValueError, "Repeated"):
                    validate_study(p)

    def test_reject_missing_arm_and_duplicate_order(self):
        for key in ("arm", "order"):
            with self.subTest(key=key):
                p = fixture()
                p["blocks"][0]["trials"][0][key] = p["blocks"][0]["trials"][1][key]
                with self.assertRaises(ValueError):
                    validate_study(p)

    def test_reject_timepoint_as_analysis_unit(self):
        self.plan["analysis_unit"] = "sample"
        with self.assertRaisesRegex(ValueError, "matched impact block"):
            validate_study(self.plan)

    def test_reject_human_origin(self):
        for origin in ("HUMAN", "ATHLETE_EEG", "UNREVIEWED"):
            self.plan["origin"] = origin
            with self.assertRaisesRegex(ValueError, "nonhuman"):
                validate_study(self.plan)

    def test_reject_evidence_promotion(self):
        self.plan["evidence_tier"] = "S2"
        with self.assertRaisesRegex(ValueError, "exactly"):
            validate_study(self.plan)

    def test_reject_nonfinite_numbers(self):
        self.plan["blocks"][0]["temperature_c"] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite"):
            validate_study(self.plan)

    def test_reject_primary_outcome_as_secondary(self):
        self.plan["secondary_outcomes"] = [self.plan["primary_outcome"]]
        with self.assertRaisesRegex(ValueError, "Secondary"):
            validate_study(self.plan)

    def test_reject_unknown_outcome_or_boolean_tolerance(self):
        self.plan["primary_outcome"] = "concussion_risk"
        with self.assertRaises(ValueError):
            validate_study(self.plan)
        self.plan = fixture()
        self.plan["max_speed_deviation_m_s"] = True
        with self.assertRaises(ValueError):
            validate_study(self.plan)

    def test_reject_duplicate_json_keys(self):
        self.path.write_text('{"schema_version":"neuroshield.study-design/0.1","schema_version":"bad"}')
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            read_study(self.path)

    def test_reject_symlinked_plan(self):
        alias = self.root / "alias.json"
        try:
            alias.symlink_to(self.path)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink unavailable")
        with self.assertRaisesRegex(ValueError, "symlinked"):
            read_study(alias)

    def test_cli_refuses_overwrite(self):
        out = self.root / "result.json"
        out.write_text("KEEP")
        with redirect_stdout(StringIO()), self.assertRaises(SystemExit) as caught:
            main([str(self.path), "--out", str(out)])
        self.assertEqual(caught.exception.code, 2)
        self.assertEqual(out.read_text(), "KEEP")

    def test_cli_report_has_no_raw_impacts(self):
        out = self.root / "report.json"
        with redirect_stdout(StringIO()):
            self.assertEqual(main([str(self.path), "--out", str(out)]), 0)
        report = json.loads(out.read_text())
        self.assertEqual(report["scientific_evidence_level"], "S0")
        self.assertNotIn("trials", report)


if __name__ == "__main__":
    unittest.main()
