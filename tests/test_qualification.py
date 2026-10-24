"""Numerical refinement and synthetic-only interchange safeguards."""
from copy import deepcopy
import json
import tempfile
import unittest
from pathlib import Path
from neuroshield.models import Parameters, SCENARIOS
from neuroshield.physics import simulate
from neuroshield.qualification import qualify, DT_LEVELS_S
from neuroshield.session import synthetic_fixture, validate_session, validate_session_file


class RefinementTests(unittest.TestCase):
    def test_time_step_reproducibility_and_fingerprint(self):
        a=simulate("oblique", dt=0.00025)
        self.assertEqual(a, simulate("oblique", dt=0.00025))
        self.assertEqual(len(a["traces"]["time_ms"]),1001)
        self.assertNotEqual(a["provenance"]["scientific_fingerprint"],simulate("oblique")["provenance"]["scientific_fingerprint"])
        for dt in (0,-.01,.002,.0003,float('nan'),True):
            with self.subTest(dt=dt), self.assertRaises(ValueError):
                simulate("oblique",dt=dt)

    def test_qualify_all_scenarios_both_designs(self):
        for scene in SCENARIOS:
            for params in (Parameters(),Parameters.suggested()):
                with self.subTest(scenario=scene,params=params):
                    out=qualify(scene,params)
                    self.assertEqual(out["step_sizes_s"],DT_LEVELS_S)
                    self.assertEqual(len(out["metrics"]),5)
                    self.assertEqual(len(out["report_sha256"]),64)
                    self.assertEqual(out,qualify(scene,params))
                    self.assertFalse("clinically" in out["status"].lower())

    def test_strict_qualification_parameters(self):
        for invalid in (0,1,float('nan'),True):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                qualify("oblique",tolerance=invalid)
        with self.assertRaises(ValueError):
            qualify("nope")


class SessionTests(unittest.TestCase):
    def test_roundtrip_and_no_identifiers(self):
        example=synthetic_fixture()
        report=validate_session(example)
        self.assertTrue(report["valid"])
        self.assertEqual(report["channels"]["eeg_f3"]["low_quality_samples"],10)
        self.assertEqual(report,validate_session(deepcopy(example)))
        with tempfile.TemporaryDirectory() as temp:
            file=Path(temp)/"synthetic.json"
            file.write_text(json.dumps(example))
            self.assertEqual(report,validate_session_file(file))

    def test_reject_real_and_bad_timestamp_quality_and_units(self):
        baseline=synthetic_fixture()
        modifications=[
            lambda x:x.update(data_origin="real"),
            lambda x:x.update(subject_id="secret"),
            lambda x:x.update(session_id="PERSON-01"),
            lambda x:x["channels"]["eeg_f3"].update(unit="V"),
            lambda x:x["channels"]["eeg_f3"]["time_s"].__setitem__(2,0),
            lambda x:x["channels"]["eeg_f3"]["quality"].__setitem__(0,1.5),
            lambda x:x["channels"]["eeg_f3"]["values"].__setitem__(0,float('nan')),
            lambda x:x["channels"]["eeg_f3"]["quality"].pop(),
        ]
        for change in modifications:
            bad=deepcopy(baseline)
            change(bad)
            with self.subTest(change=change),self.assertRaises(ValueError):
                validate_session(bad)

    def test_gap_counter_and_missing_channel(self):
        fixture=synthetic_fixture()
        fixture["channels"]["eeg_f3"]["time_s"][80:]=[round(t+.05,3) for t in fixture["channels"]["eeg_f3"]["time_s"][80:]]
        self.assertEqual(validate_session(fixture)["channels"]["eeg_f3"]["timing_gaps"],1)
        fixture["channels"]["animal_id"]={}
        with self.assertRaises(ValueError):validate_session(fixture)
