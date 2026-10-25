"""Independent S0 waveform screening regression tests (all fixtures synthetic)."""
import json
import math
import shutil
import tempfile
import unittest
from pathlib import Path

from neuroshield.waveform_qualification import read_plan, evaluate_pair, model_vs_measurement_gate
from neuroshield.headform import validate_headform_bundle

ROOT = Path(__file__).resolve().parents[1] / "examples"


class WaveformTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.plan = self.base / "plan.json"
        shutil.copy2(ROOT / "paired-waveform-plan-SYNTHETIC.json", self.plan)
        for key in ("reference", "candidate"):
            for kind in ("profile.json", "manifest.json", "csv"):
                src = ROOT / (f"bench-{key}-SYNTHETIC.{kind}" if kind == "csv" else f"bench-{key}-SYNTHETIC-{kind}")
                shutil.copy2(src, self.base / f"{key}-{kind}")

    def triple(self, name):
        return (self.base / f"{name}-profile.json", self.base / f"{name}-manifest.json", self.base / f"{name}-csv")

    def run_pair(self):
        return evaluate_pair(self.plan, self.triple("reference"), self.triple("candidate"))

    def change_plan(self, fn):
        p = json.loads(self.plan.read_text())
        fn(p)
        self.plan.write_text(json.dumps(p))

    def change_manifest(self, name, fn):
        path = self.triple(name)[1]
        p = json.loads(path.read_text())
        fn(p)
        path.write_text(json.dumps(p))
        self.rehash(name)

    def change_profile(self, name, fn):
        path = self.triple(name)[0]
        p = json.loads(path.read_text())
        fn(p)
        path.write_text(json.dumps(p))

    def rehash(self, name):
        prof, manifest, csv_file = self.triple(name)
        p = json.loads(prof.read_text())
        s = validate_headform_bundle(manifest, csv_file)
        p["headform_bundle_sha256"] = s["bundle_sha256"]
        p["source"]["raw_data_sha256"] = s["csv_sha256"]
        prof.write_text(json.dumps(p))

    def test_reproducible_trace_metrics_and_alerts(self):
        a, b = self.run_pair(), self.run_pair()
        self.assertEqual(a,b)
        self.assertEqual(a["sample_count"],51)
        self.assertEqual(a["scientific_evidence_level"],"S0")
        self.assertEqual(a["status"],"SYNTHETIC_SCREEN_ONLY")
        self.assertEqual(len(a["alerts"]),4)
        self.assertAlmostEqual(a["metrics"]["linear_acceleration_m_s2"]["changes_percent"]["rms"],-10)
        self.assertAlmostEqual(a["metrics"]["angular_acceleration_rad_s2"]["changes_percent"]["peak"],10)
        self.assertNotIn("raw",str(a))
        self.assertNotIn(str(self.base),str(a))

    def test_waveform_rms_integral_and_shape_are_well_defined(self):
        metrics = self.run_pair()["metrics"]
        for k,m in metrics.items():
            self.assertGreater(m["reference"]["peak"],0)
            self.assertGreater(m["candidate"]["trapezoid_integral"],0)
            self.assertAlmostEqual(m["shape_comparison"]["pearson_correlation"],1,places=11)
            self.assertAlmostEqual(m["reference"]["window_duration_s"],.025)
            self.assertTrue(math.isfinite(m["shape_comparison"]["normalized_rmse_to_reference_rms"]))

    def test_invalid_alignment_rejected(self):
        self.change_plan(lambda p: p.update(alignment_policy="optimize_lag"))
        with self.assertRaisesRegex(ValueError,"Clock shifting"):
            self.run_pair()

    def test_window_outside_samples_rejected(self):
        self.change_plan(lambda p: p.update(window_s=[.002,.030]))
        with self.assertRaisesRegex(ValueError,"window not fully covered"):
            self.run_pair()

    def test_short_window_rejected(self):
        self.change_plan(lambda p: p.update(window_s=[0.0,.0005]))
        with self.assertRaisesRegex(ValueError,"three or more samples"):
            self.run_pair()

    def test_duplicate_window_rejected(self):
        self.change_plan(lambda p: p.update(window_s=[.01,.01]))
        with self.assertRaisesRegex(ValueError,"positive duration"):
            read_plan(self.plan)

    def test_unknown_plan_fields_and_bad_limit_rejected(self):
        self.change_plan(lambda p: p.update(athlete_identifier="private"))
        with self.assertRaisesRegex(ValueError,"exact"):
            self.run_pair()
        shutil.copy2(ROOT/"paired-waveform-plan-SYNTHETIC.json",self.plan)
        self.change_plan(lambda p: p["limits"]["angular_velocity_rad_s"].update(max_rms_increase_pct=float('nan')))
        with self.assertRaisesRegex(ValueError,"finite"):
            self.run_pair()

    def test_preregistered_threshold_change_changes_alert_only(self):
        self.change_plan(lambda p: [threshold.update(max_peak_increase_pct=12.0,max_rms_increase_pct=12.0) for threshold in p["limits"].values()])
        r = self.run_pair()
        self.assertEqual(r["screen"],"NO_PREREGISTERED_ALERTS_OBSERVED")
        self.assertEqual(r["scientific_evidence_level"],"S0")

    def test_rights_pending_real_origin_fail_closed(self):
        for label in ("reference","candidate"):
            self.change_manifest(label,lambda m:m.update(origin="NONHUMAN_INSTRUMENTED_HEADFORM"))
            self.change_profile(label,lambda p:p.update(origin="NONHUMAN_INSTRUMENTED_HEADFORM"))
            self.change_profile(label,lambda p:p["source"].update(source_uri="https://example.org/headform-test"))
        with self.assertRaisesRegex(ValueError,"Unreviewed real-data rights"):
            self.run_pair()

    def test_mixed_origin_rejected(self):
        self.change_manifest("candidate",lambda m:m.update(origin="NONHUMAN_INSTRUMENTED_HEADFORM"))
        self.change_profile("candidate",lambda p:p.update(origin="NONHUMAN_INSTRUMENTED_HEADFORM"))
        self.change_profile("candidate",lambda p:p["source"].update(source_uri="https://example.org/headform-test"))
        self.change_profile("candidate",lambda p:p["rights"].update(review_status="documented_local_analysis"))
        with self.assertRaisesRegex(ValueError,"Cannot mix"):
            self.run_pair()

    def test_manifest_protocol_mismatch_rejected(self):
        self.change_manifest("candidate",lambda m:m.update(test_protocol="DIFFERENT"))
        with self.assertRaisesRegex(ValueError,"test_protocol"):
            self.run_pair()

    def test_clock_mismatch_rejected_even_with_valid_profile_hash(self):
        csv_file = self.triple("candidate")[2]
        lines = csv_file.read_text().splitlines()
        for i in range(1,len(lines)):
            col = lines[i].split(',')
            col[0]=f"{float(col[0])+.00010:.6f}"
            lines[i]=','.join(col)
        csv_file.write_text('\n'.join(lines)+'\n')
        self.rehash("candidate")
        with self.assertRaisesRegex(ValueError,"Clock mismatch"):
            self.run_pair()

    def test_clock_jitter_below_gap_threshold_rejected(self):
        csv_file = self.triple("candidate")[2]
        lines = csv_file.read_text().splitlines()
        col = lines[21].split(',')
        col[0] = f"{float(col[0]) + .00006:.6f}"
        lines[21] = ','.join(col)
        csv_file.write_text('\n'.join(lines)+'\n')
        ref_csv = self.triple("reference")[2]
        ref_csv.write_text('\n'.join(lines)+'\n')
        # Both clocks share the same jitter; mismatch is not the failure condition.
        for name in ("reference", "candidate"):
            self.rehash(name)
        with self.assertRaisesRegex(ValueError, "clock jitter"):
            self.run_pair()

    def test_tamper_hash_rejected(self):
        csv_file=self.triple("reference")[2]
        csv_file.write_text(csv_file.read_text().replace('0.6279050','0.9279050'))
        with self.assertRaisesRegex(ValueError,"hash mismatch"):
            self.run_pair()

    def test_sampling_rate_and_paired_speed_gate(self):
        self.change_profile("candidate",lambda p:p["acquisition"].update(impact_speed_m_s=6))
        with self.assertRaisesRegex(ValueError,"Impact speeds"):
            self.run_pair()

    def test_direct_model_fit_gate_is_blocked(self):
        a = model_vs_measurement_gate({"assumption":"1D"},{"source_origin":"SYNTHETIC_HEADFORM_FIXTURE"})
        self.assertEqual(a["status"],"BLOCKED")
        self.assertIn("REAL_HEADFORM_DATA_UNAVAILABLE",a["reasons"])
        b = model_vs_measurement_gate({"assumption":"1D"},{"source_origin":"NONHUMAN_INSTRUMENTED_HEADFORM"})
        self.assertEqual(b["status"],"BLOCKED")
        self.assertNotIn("REAL_HEADFORM_DATA_UNAVAILABLE",b["reasons"])


if __name__ == "__main__":
    unittest.main()
