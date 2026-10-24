"""Regression checks for pre-step synchronization and read-only headform contract."""
import csv
import json
import math
import tempfile
import unittest
from pathlib import Path

from neuroshield.headform import COLUMNS, UNITS, validate_headform_bundle
from neuroshield.models import SCENARIOS
from neuroshield.physics import simulate
from neuroshield.independent_qualification import qualify_independent
from neuroshield.qualification import qualify


class TraceClockTests(unittest.TestCase):
    def test_velocity_and_angle_are_at_same_instant_as_acceleration(self):
        h = 0.000125
        for scene in SCENARIOS:
            with self.subTest(scene=scene):
                result = simulate(scene, dt=h, include_audit_traces=True)
                series = result["audit_traces"]
                self.assertEqual(len(series["time_s"]), 2001)
                self.assertEqual(series["time_s"][0], 0)
                self.assertAlmostEqual(series["time_s"][-1], 0.25)
                self.assertEqual(result["provenance"]["sample_semantics"],
                                 "pre_step_state_and_acceleration_at_time_t")
                for i in (0, 1, 2, 10, 52, 500, 1999):
                    self.assertAlmostEqual(
                        series["head_omega_rad_s"][i+1] - series["head_omega_rad_s"][i],
                        h*series["head_angular_accel_rad_s2"][i], delta=1e-13)
                    self.assertAlmostEqual(
                        series["head_relative_torso_rad"][i+1] - series["head_relative_torso_rad"][i],
                        h*series["head_omega_rad_s"][i+1], delta=1e-13)
                metrics = result["metrics_unrounded"]
                self.assertAlmostEqual(metrics["peak_head_accel_g"],
                    max(map(abs, series["head_linear_g"])), places=12)
                self.assertAlmostEqual(metrics["peak_angular_accel_rad_s2"],
                    max(map(abs, series["head_angular_accel_rad_s2"])), places=12)
                self.assertAlmostEqual(metrics["peak_head_angular_speed_rad_s"],
                    max(map(abs, series["head_omega_rad_s"])), places=12)
                self.assertTrue(all(math.isfinite(v) for arr in series.values() for v in arr))

    def test_opt_in_only_and_unrounded_qualification(self):
        default = simulate("oblique")
        self.assertNotIn("audit_traces", default)
        self.assertIsNone(default["provenance"]["audit_trace_sha256"])
        full = simulate("oblique", include_audit_traces=True)
        self.assertEqual(full["metrics_unrounded"], default["metrics_unrounded"])
        self.assertEqual(len(full["provenance"]["audit_trace_sha256"]), 64)
        self.assertEqual(full, simulate("oblique", include_audit_traces=True))
        self.assertNotEqual(full["metrics_unrounded"]["peak_head_accel_g"],
                            full["metrics"]["peak_head_accel_g"])
        with self.assertRaises(ValueError):
            simulate(include_audit_traces=1)
        refined = qualify("oblique")
        self.assertIn("unrounded", refined["comparison"])
        independent = qualify_independent("oblique")
        cell = independent["cases"][0]["metric_comparison"]["peak_head_accel_g"]
        self.assertIn("primary_unrounded", cell)


class HeadformManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.manifest = Path(self.tmp.name) / "manifest.json"
        self.csvfile = Path(self.tmp.name) / "fixture.csv"
        self.meta = {
            "schema_version": "0.1.0", "origin": "SYNTHETIC_HEADFORM_FIXTURE",
            "fixture_id": "demo-001", "condition": "reference",
            "impact_location": "facemask", "rig_id": "not-an-actual-rig",
            "sensor_alias": "synthetic", "calibration_reference": "NOT-CALIBRATED-SYNTHETIC",
            "test_protocol": "SYNTHETIC_DEMO_ONLY", "coordinate_frame": "right_handed_headform_body",
            "units": dict(UNITS),
        }
        self.rows = [[i/1000, *([float(i)]*9)] for i in range(5)]

    def write(self):
        self.manifest.write_text(json.dumps(self.meta))
        with self.csvfile.open("w", newline="") as file:
            w = csv.writer(file)
            w.writerow(COLUMNS)
            w.writerows(self.rows)
        return validate_headform_bundle(self.manifest, self.csvfile)

    def test_determinism_and_no_raw_traces(self):
        out = self.write()
        self.assertEqual(out, self.write())
        self.assertEqual(out["rows"], 5)
        self.assertEqual(out["status"], "STRUCTURE_ONLY_NOT_CALIBRATION")
        self.assertNotIn("samples", out)
        self.assertEqual(out["possible_missing_sample_gaps"], 0)
        self.assertEqual(len(out["bundle_sha256"]), 64)

    def test_rejects_human_data_unknown_frames_and_units(self):
        self.meta["origin"] = "HUMAN_PLAYER"
        with self.assertRaisesRegex(ValueError, "human"):
            self.write()
        self.meta["origin"] = "SYNTHETIC_HEADFORM_FIXTURE"
        self.meta["units"]["angular_acceleration"] = "deg/s^2"
        with self.assertRaisesRegex(ValueError, "SI units"):
            self.write()
        self.meta["units"] = dict(UNITS)
        self.meta["coordinate_frame"] = "unknown"
        with self.assertRaisesRegex(ValueError, "right_handed"):
            self.write()

    def test_rejects_nonfinite_duplicate_timestamps_and_csv_extra_columns(self):
        self.rows[2][0] = self.rows[1][0]
        with self.assertRaisesRegex(ValueError, "nonmonotonic"):
            self.write()
        self.rows[2][0] = .002
        self.rows[2][1] = float("nan")
        with self.assertRaisesRegex(ValueError, "Non-finite"):
            self.write()
        self.rows[2][1] = 2
        self.rows[2].append("extra")
        with self.assertRaisesRegex(ValueError, "Malformed"):
            self.write()

    def test_gap_flags_do_not_imply_resampling(self):
        self.rows[3][0], self.rows[4][0] = .03, .031
        out = self.write()
        self.assertEqual(out["possible_missing_sample_gaps"], 1)


if __name__ == "__main__":
    unittest.main()
