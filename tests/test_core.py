import csv
import json
import math
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from neuroshield.analysis import comparison
from neuroshield.physics import simulate
from neuroshield.models import SCENARIOS, Parameters
from neuroshield.signals import add_synthetic_signals
from neuroshield.privacy import Consent, access_allowed, require_access, AccessDenied
from neuroshield.ingestion import validate_kinematics_csv, REQUIRED_COLUMNS
from neuroshield.cad import write_mount_visualization


class ImpactTests(unittest.TestCase):
    def test_all_scenarios_are_deterministic_and_finite(self):
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario):
                a = simulate(scenario, Parameters.suggested())
                self.assertEqual(a, simulate(scenario, Parameters.suggested()))
                self.assertFalse(a["provenance"]["clinically_validated"])
                self.assertEqual(a["provenance"]["source"], "deterministic_synthetic_simulation")
                n = len(a["traces"]["time_ms"])
                self.assertEqual(n, 501)
                self.assertEqual(a["traces"]["time_ms"][0], 0)
                self.assertEqual(a["traces"]["time_ms"][-1], 250)
                for k, arr in a["traces"].items():
                    self.assertEqual(len(arr), n, k)
                    self.assertTrue(all(math.isfinite(x) for x in arr), k)
                self.assertGreater(a["metrics"]["dissipated_energy_proxy_j"], 0)
                self.assertGreater(a["metrics"]["peak_head_accel_g"], 0)
                self.assertGreater(a["metrics"]["peak_angular_accel_rad_s2"], 0)

    def test_identity_design_zero_changes(self):
        comparison_result = comparison("facemask", Parameters())
        self.assertEqual(comparison_result["baseline"], comparison_result["candidate"])
        self.assertTrue(all(v == 0 for v in comparison_result["relative_change_pct"].values()))

    def test_suggested_design_has_tradeoffs(self):
        out = comparison("oblique", Parameters.suggested())
        self.assertNotEqual(out["candidate"]["metrics"], out["baseline"]["metrics"])
        self.assertGreater(out["relative_change_pct"]["peak_angular_accel_rad_s2"], 0,
                           "Do not accidentally hide worsening rotation behind better linear response")
        self.assertLess(out["relative_change_pct"]["peak_head_accel_g"], 0)

    def test_params_fail_closed(self):
        for invalid in [{"mount_travel_mm": 100}, {"mount_c_ns_m": -1}, {"mount_k_n_m": float("nan")},
                        {"mount_k_n_m": True}, {"magic": 1}, ["invalid"]]:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                Parameters.from_payload(invalid)
        with self.assertRaises(ValueError):
            simulate("unknown")

    def test_eeg_and_emg_are_synthetic_and_quality_gated(self):
        r = add_synthetic_signals(simulate("oblique"))
        self.assertEqual(r["signals"]["metadata"]["source"], "SYNTHETIC")
        self.assertEqual(len(r["signals"]["eeg_uV"]), 501)
        self.assertTrue(any(q < 0.5 for q in r["signals"]["eeg_signal_quality"]))
        self.assertTrue(any(q > 0.9 for q in r["signals"]["eeg_signal_quality"]))


class PrivacyTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 23, tzinfo=timezone.utc)
        self.consent = Consent(subject_id="anon-01", granted_to="licensed-clinician-42", purpose="medical_research",
                               active=True, expires_at=self.now + timedelta(days=4), scope=("eeg", "emg"))

    def test_synthetic_allowed(self):
        self.assertTrue(access_allowed(data_origin="synthetic"))

    def test_real_access_requires_exact_scope(self):
        kwargs = dict(data_origin="real", principal="licensed-clinician-42", subject_id="anon-01",
                      purpose="medical_research", modality="eeg", consents=(self.consent,), now=self.now)
        self.assertTrue(access_allowed(**kwargs))
        for item in (dict(principal="team-scout"), dict(purpose="roster_decisions"),
                     dict(modality="gps"), dict(subject_id="anon-02"), dict(consents=()),
                     dict(now=self.now + timedelta(days=5))):
            with self.subTest(item=item):
                self.assertFalse(access_allowed(**(kwargs | item)))
                with self.assertRaises(AccessDenied):
                    require_access(**(kwargs | item))

    def test_revoked_and_unknown_origins_denied(self):
        from dataclasses import replace
        self.assertFalse(access_allowed(data_origin="real", principal="licensed-clinician-42",
            subject_id="anon-01", purpose="medical_research", modality="eeg",
            consents=(replace(self.consent, active=False),), now=self.now))
        self.assertFalse(access_allowed(data_origin="missing_label"))


class IngestionTests(unittest.TestCase):
    def write(self, rows):
        d = tempfile.TemporaryDirectory()
        file = Path(d.name) / "example.csv"
        with file.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        self.addCleanup(d.cleanup)
        return file

    def good_rows(self):
        return [dict(zip(REQUIRED_COLUMNS, [i * .001, 1, 0, 0, 0, 0, .1])) for i in range(3)]

    def test_csv_schema(self):
        r = validate_kinematics_csv(self.write(self.good_rows()))
        self.assertEqual(r["rows"], 3)
        self.assertTrue(r["valid"])
        self.assertEqual(r["min_dt_s"], .001)

    def test_timestamp_and_nan_errors(self):
        r = self.good_rows()
        r[2]["time_s"] = r[1]["time_s"]
        with self.assertRaisesRegex(ValueError, "non-monotonic"):
            validate_kinematics_csv(self.write(r))
        r = self.good_rows()
        r[0]["head_ax_m_s2"] = "NaN"
        with self.assertRaisesRegex(ValueError, "non-finite"):
            validate_kinematics_csv(self.write(r))

    def test_mount_is_nonfunctional_preview(self):
        with tempfile.TemporaryDirectory() as d:
            file = write_mount_visualization(Path(d) / "preview.scad", Parameters.suggested())
            content = file.read_text()
            self.assertIn("NEVER INSTALL", content)
            self.assertIn("travel_mm = 7.000", content)


if __name__ == "__main__":
    unittest.main()

class KinematicsTests(unittest.TestCase):
    def test_relative_orientation_and_coordinate_invariance(self):
        from neuroshield.kinematics import Quaternion, relative_angle_deg, relative_angular_velocity_torso_frame
        turn=Quaternion.axis_angle((0,0,1),math.pi/6)
        identity=Quaternion(1,0,0,0)
        self.assertAlmostEqual(relative_angle_deg(turn,identity),30,places=8)
        self.assertAlmostEqual(relative_angle_deg(turn,turn),0,places=8)
        # Same motion relative to either world orientation.
        torso=Quaternion.axis_angle((1,0,0),math.pi/4)
        head=torso.multiply(turn)
        self.assertAlmostEqual(relative_angle_deg(head,torso),30,places=8)
        v=relative_angular_velocity_torso_frame(identity,identity,(0,0,2),(0,0,.5))
        self.assertAlmostEqual(v[2],1.5,places=8)
        r=turn.rotate((1,0,0))
        self.assertAlmostEqual(r[0],math.cos(math.pi/6),places=8)
        self.assertAlmostEqual(r[1],math.sin(math.pi/6),places=8)

    def test_gap_aware_alignment(self):
        from neuroshield.kinematics import interpolate_no_gaps
        self.assertEqual(interpolate_no_gaps([0,.01,.20],[0,10,100],[-1,0,.005,.03,.2,.3]),
                         [None,0,5,None,100,None])
        with self.assertRaises(ValueError):
            interpolate_no_gaps([0,.1,.1],[1,2,3],[.05])

    def test_fingerprint_parameter_and_source_provenance(self):
        one=simulate("oblique")
        two=simulate("oblique")
        changed=simulate("oblique",Parameters.suggested())
        self.assertEqual(one["provenance"],two["provenance"])
        self.assertNotEqual(one["provenance"]["scientific_fingerprint"],
                            changed["provenance"]["scientific_fingerprint"])
        self.assertEqual(len(one["provenance"]["execution_trace_sha256"]),64)

class DesignSpaceTests(unittest.TestCase):
    def test_pareto_grid_is_bounded_and_nonempty(self):
        from neuroshield.design_space import sweep, KEYS, _dominates
        out=sweep()
        self.assertEqual(out["candidate_count"],36)
        self.assertGreater(out["pareto_count"],0)
        self.assertFalse(out["model_clinically_validated"])
        vectors=[list(c["worst_case_ratios"].values()) for c in out["pareto_frontier"]]
        self.assertTrue(all(len(v)==len(KEYS) for v in vectors))
        self.assertTrue(all(not _dominates(a,b) for i,a in enumerate(vectors) for j,b in enumerate(vectors) if i!=j))
