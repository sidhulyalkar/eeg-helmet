"""Offline, fail-closed synthetic bench intake regression tests."""
import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from neuroshield.bench_intake import compare_paired_trials, validate_intake
from neuroshield.headform import validate_headform_bundle

ROOT = Path(__file__).resolve().parents[1] / "examples"


class BenchIntakeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for label in ("reference", "candidate"):
            for suffix in ("profile.json", "manifest.json", "csv"):
                src = ROOT / (f"bench-{label}-SYNTHETIC.csv" if suffix == "csv" else f"bench-{label}-SYNTHETIC-{suffix}")
                shutil.copy2(src, self.root / f"{label}-{suffix}")

    def paths(self, condition):
        return (self.root / f"{condition}-profile.json", self.root / f"{condition}-manifest.json", self.root / f"{condition}-csv")

    def patch_profile(self, condition, edit):
        p, manifest, csv_file = self.paths(condition)
        data = json.loads(p.read_text())
        edit(data)
        p.write_text(json.dumps(data))

    def patch_manifest(self, condition, edit):
        p, m, csv_file = self.paths(condition)
        data = json.loads(m.read_text())
        edit(data)
        m.write_text(json.dumps(data))
        self.refresh_hashes(condition)

    def patch_csv(self, condition, edit):
        p, m, csv_file = self.paths(condition)
        with csv_file.open(newline="") as f:
            rows = list(csv.reader(f))
        edit(rows)
        with csv_file.open("w", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerows(rows)
        self.refresh_hashes(condition)

    def refresh_hashes(self, condition):
        p, m, csv_file = self.paths(condition)
        meta = json.loads(p.read_text())
        try:
            bundle = validate_headform_bundle(m, csv_file)
        except ValueError:
            return
        meta["headform_bundle_sha256"] = bundle["bundle_sha256"]
        meta["source"]["raw_data_sha256"] = bundle["csv_sha256"]
        p.write_text(json.dumps(meta))

    def test_intake_deterministic_and_fails_closed_on_synthetic(self):
        summary = validate_intake(*self.paths("reference"))
        self.assertEqual(summary, validate_intake(*self.paths("reference")))
        self.assertEqual(summary["intake_status"], "BLOCKED")
        self.assertEqual(summary["scientific_evidence_level"], "S0")
        self.assertIn("SYNTHETIC_NOT_PHYSICAL_EVIDENCE", summary["blockers"])
        self.assertNotIn("raw", str(summary))
        self.assertNotIn(str(self.root), str(summary))
        self.assertEqual(summary["trace_count"], 51)

    def test_synthetic_pair_trades_off_linear_and_angular(self):
        report = compare_paired_trials(self.paths("reference"), self.paths("candidate"))
        self.assertEqual(report["status"], "DEMONSTRATION_ONLY")
        self.assertEqual(report, compare_paired_trials(self.paths("reference"), self.paths("candidate")))
        metrics = report["metrics"]
        self.assertAlmostEqual(metrics["resultant_linear_acceleration_m_s2"]["peak_percent_change"], -10)
        self.assertAlmostEqual(metrics["resultant_angular_acceleration_rad_s2"]["peak_percent_change"], 10)
        self.assertEqual(metrics["resultant_linear_acceleration_m_s2"]["separation"], "lower")
        self.assertEqual(metrics["resultant_angular_acceleration_rad_s2"]["separation"], "higher")
        self.assertIn("NO_NECK_LOAD_MEASURED", report["blockers"])
        self.assertNotIn("samples", report)
        self.assertEqual(report["scientific_evidence_level"], "S0")

    def test_tampered_csv_rejected_by_hash(self):
        csv_file = self.paths("reference")[2]
        contents = csv_file.read_text()
        csv_file.write_text(contents.replace("0.627905", "0.627906"))
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            validate_intake(*self.paths("reference"))

    def test_origin_cannot_turn_synthetic_into_measured(self):
        self.patch_profile("reference", lambda d: d.update(origin="NONHUMAN_INSTRUMENTED_HEADFORM"))
        self.patch_profile("reference", lambda d: d["source"].update(source_uri="https://example.org/local-lab"))
        with self.assertRaisesRegex(ValueError, "origin mismatch"):
            validate_intake(*self.paths("reference"))

    def test_bad_units_and_human_origin_rejected(self):
        self.patch_manifest("reference", lambda d: d.update(origin="HUMAN_ATHLETE"))
        with self.assertRaisesRegex(ValueError, "human"):
            validate_intake(*self.paths("reference"))
        self.patch_manifest("reference", lambda d: d.update(origin="SYNTHETIC_HEADFORM_FIXTURE"))
        self.patch_manifest("reference", lambda d: d["units"].update(angular_velocity="deg/s"))
        with self.assertRaisesRegex(ValueError, "SI units"):
            validate_intake(*self.paths("reference"))

    def test_rights_flags_consistent_and_do_not_promote_evidence(self):
        self.patch_profile("reference", lambda d: d["rights"].update(redistribution_allowed=True))
        with self.assertRaisesRegex(ValueError, "redistribution"):
            validate_intake(*self.paths("reference"))
        self.patch_profile("reference", lambda d: d["rights"].update(review_status="documented_redistribution"))
        report = validate_intake(*self.paths("reference"))
        self.assertEqual(report["intake_status"], "BLOCKED")
        self.assertEqual(report["scientific_evidence_level"], "S0")

    def test_sampling_rate_mismatch_rejected(self):
        self.patch_profile("reference", lambda d: d["acquisition"].update(sampling_hz=1200))
        with self.assertRaisesRegex(ValueError, "sampling frequency"):
            validate_intake(*self.paths("reference"))

    def test_saturation_blocks_pair(self):
        self.patch_profile("reference", lambda d: d["acquisition"].update(sensor_angular_fullscale_rad_s2=120.0))
        self.assertIn("POSSIBLE_SENSOR_SATURATION", validate_intake(*self.paths("reference"))["blockers"])
        with self.assertRaisesRegex(ValueError, "missing samples or saturation"):
            compare_paired_trials(self.paths("reference"), self.paths("candidate"))

    def test_missing_samples_block_pair(self):
        def gap(rows):
            for i in range(26, len(rows)):
                rows[i][0] = f"{float(rows[i][0]) + .005:.6f}"
        self.patch_csv("reference", gap)
        result = validate_intake(*self.paths("reference"))
        self.assertIn("POSSIBLE_SAMPLE_GAPS", result["blockers"])
        with self.assertRaisesRegex(ValueError, "missing samples or saturation"):
            compare_paired_trials(self.paths("reference"), self.paths("candidate"))

    def test_mismatched_protocol_rejected(self):
        self.patch_manifest("candidate", lambda d: d.update(impact_location="rear"))
        with self.assertRaisesRegex(ValueError, "impact_location"):
            compare_paired_trials(self.paths("reference"), self.paths("candidate"))

    def test_mismatched_filter_and_impactor_speed_rejected(self):
        self.patch_profile("candidate", lambda d: d["acquisition"].update(filter_reference="DIFFERENT"))
        with self.assertRaisesRegex(ValueError, "filter_reference"):
            compare_paired_trials(self.paths("reference"), self.paths("candidate"))
        self.patch_profile("candidate", lambda d: d["acquisition"].update(filter_reference="FAKE_NO_FILTER", impact_speed_m_s=6.0))
        with self.assertRaisesRegex(ValueError, "Impact speeds"):
            compare_paired_trials(self.paths("reference"), self.paths("candidate"))

    def test_mismatched_clock_rejected_without_interpolation(self):
        self.patch_csv("candidate", lambda rows: [r.__setitem__(0, f"{float(r[0])+.0001:.6f}") for r in rows[1:]])
        with self.assertRaisesRegex(ValueError, "clock mismatch"):
            compare_paired_trials(self.paths("reference"), self.paths("candidate"))

    def test_measured_record_requires_rights_review_before_pairing(self):
        for label in ("reference", "candidate"):
            self.patch_manifest(label, lambda d: d.update(origin="NONHUMAN_INSTRUMENTED_HEADFORM"))
            self.patch_profile(label, lambda d: d.update(origin="NONHUMAN_INSTRUMENTED_HEADFORM"))
            self.patch_profile(label, lambda d: d["source"].update(source_uri="https://example.org/nonhuman-bench-test"))
        with self.assertRaisesRegex(ValueError, "rights review pending"):
            compare_paired_trials(self.paths("reference"), self.paths("candidate"))

    def test_invalid_nonfinite_uncertainty_rejected(self):
        self.patch_profile("reference", lambda d: d["uncertainty"].update(linear_acceleration_m_s2=float("nan")))
        with self.assertRaisesRegex(ValueError, "must be finite"):
            validate_intake(*self.paths("reference"))

    def test_unknown_profile_fields_rejected(self):
        self.patch_profile("reference", lambda d: d.update(athlete_id="PRIVATE"))
        with self.assertRaisesRegex(ValueError, "exact fields"):
            validate_intake(*self.paths("reference"))

    def test_real_origin_requires_https_and_still_requires_review(self):
        self.patch_manifest("reference", lambda d: d.update(origin="NONHUMAN_INSTRUMENTED_HEADFORM"))
        self.patch_profile("reference", lambda d: d.update(origin="NONHUMAN_INSTRUMENTED_HEADFORM"))
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            validate_intake(*self.paths("reference"))
        self.patch_profile("reference", lambda d: d["source"].update(source_uri="https://example.org/private-test-manifest"))
        report = validate_intake(*self.paths("reference"))
        self.assertEqual(report["intake_status"], "BLOCKED")
        self.assertIn("INDEPENDENT_CALIBRATION_AND_LAB_REVIEW_REQUIRED", report["blockers"])
        self.patch_profile("reference", lambda d: d["rights"].update(review_status="documented_local_analysis"))
        report = validate_intake(*self.paths("reference"))
        self.assertEqual(report["intake_status"], "REVIEW_REQUIRED")
        self.assertEqual(report["scientific_evidence_level"], "S0")


if __name__ == "__main__":
    unittest.main()
