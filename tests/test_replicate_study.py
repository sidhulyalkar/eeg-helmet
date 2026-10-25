"""Nonhuman paired-trial replication is descriptive only; fixtures are synthetic."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from neuroshield.headform import validate_headform_bundle
from neuroshield.replicate_study import CHANNELS, SCHEMA, evaluate_study

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"

class ReplicateStudyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.pairs = []
        for i in range(3):
            pair = {}
            for arm in ("reference", "candidate"):
                triple = {}
                for kind in ("profile", "manifest", "csv"):
                    src = EXAMPLES / (f"bench-{arm}-SYNTHETIC.csv" if kind == "csv" else f"bench-{arm}-SYNTHETIC-{kind}.json")
                    dest = self.base / f"{i}-{arm}-{kind}.{ 'csv' if kind == 'csv' else 'json'}"
                    shutil.copy2(src,dest)
                    triple[kind] = dest.name
                csv = self.base / triple["csv"]
                # Create a distinct (still synthetic) recording for every trial.
                lines = csv.read_text().splitlines()
                for row in range(1, len(lines)):
                    fields=lines[row].split(",")
                    fields[1] = f"{float(fields[1])*(1 + i * .008):.9f}"
                    lines[row] = ",".join(fields)
                csv.write_text("\n".join(lines) + "\n")
                profile_path = self.base / triple["profile"]
                profile = json.loads(profile_path.read_text())
                profile["acquisition"]["replicate_id"] = f"{arm}-{i}"
                profile["acquisition"]["trial_id"] = f"study-{i}"
                bundle = validate_headform_bundle(self.base/triple["manifest"],csv)
                profile["headform_bundle_sha256"] = bundle["bundle_sha256"]
                profile["source"]["raw_data_sha256"] = bundle["csv_sha256"]
                profile_path.write_text(json.dumps(profile))
                pair[arm] = triple
            self.pairs.append(pair)
        self.plan = {"schema_version":SCHEMA,"plan_id":"synthetic-repeatability-v09","scope":"NONHUMAN_PAIRED_IMPACT_TRIALS",
                     "expected_origin":"SYNTHETIC_HEADFORM_FIXTURE","protocol":"NOT_A_REAL_PROTOCOL","impact_location":"facemask","rig_id":"NO_RIG_SIMULATED",
                     "target_speed_m_s":5.0,"speed_tolerance_m_s":.05,
                     "max_peak_regression_percent":{k:0.0 for k in CHANNELS},"pairs":self.pairs}
        self.study=self.base / "study.json"
        self.save()

    def save(self):self.study.write_text(json.dumps(self.plan))
    def test_deterministic_and_no_protection_claim(self):
        a=evaluate_study(self.study);b=evaluate_study(self.study)
        self.assertEqual(a,b)
        self.assertEqual(a["pair_count"],3)
        self.assertEqual(a["scientific_evidence_level"],"S0")
        self.assertEqual(a["screen"],"REGRESSIONS_FLAGGED")
        self.assertIn("SYNTHETIC_ONLY",a["blockers"])
        self.assertEqual(len(a["trials"]),3)
        self.assertNotIn(str(self.base),str(a))
    def test_threshold_screen_not_safety_pass(self):
        for k in CHANNELS:self.plan["max_peak_regression_percent"][k]=100
        self.save();a=evaluate_study(self.study)
        self.assertEqual(a["screen"],"NO_PREDECLARED_REGRESSIONS_FLAGGED")
        self.assertEqual(a["scientific_evidence_level"],"S0")
    def test_requires_multiple_trials(self):
        self.plan["pairs"]=self.pairs[:1];self.save()
        with self.assertRaisesRegex(ValueError,"At least two"):evaluate_study(self.study)
    def test_rejects_reused_raw_file(self):
        self.pairs[2]=self.pairs[0];self.save()
        with self.assertRaisesRegex(ValueError,"Repeated raw acquisition"):evaluate_study(self.study)
    def test_rejects_path_traversal(self):
        self.pairs[0]["reference"]["csv"]="../private.csv";self.save()
        with self.assertRaisesRegex(ValueError,"traversal"):evaluate_study(self.study)
    def test_rejects_symlink(self):
        name=self.pairs[0]["reference"]["csv"]
        path=self.base / name;actual=self.base / "raw-copy.csv";path.rename(actual);path.symlink_to(actual)
        with self.assertRaisesRegex(ValueError,"Symlinks"):evaluate_study(self.study)
    def test_rejects_unregistered_metric(self):
        self.plan["max_peak_regression_percent"]["concussion_probability"] = 0;self.save()
        with self.assertRaisesRegex(ValueError,"channel"):evaluate_study(self.study)
    def test_rejects_wrong_speed(self):
        self.plan["target_speed_m_s"]=6.0;self.save()
        with self.assertRaisesRegex(ValueError,"speed outside"):evaluate_study(self.study)
    def test_rejects_human_origin(self):
        self.plan["expected_origin"]="HUMAN";self.save()
        with self.assertRaisesRegex(ValueError,"Human data"):evaluate_study(self.study)
    def test_rejects_study_protocol_change(self):
        self.plan["protocol"]="OTHER";self.save()
        with self.assertRaisesRegex(ValueError,"preregistration"):evaluate_study(self.study)
    def test_rejects_boolean_limit(self):
        self.plan["max_peak_regression_percent"][CHANNELS[0]]=True;self.save()
        with self.assertRaisesRegex(ValueError,"finite"):evaluate_study(self.study)
    def test_rejects_unknown_plan_fields(self):
        self.plan["patient_name"]="secret";self.save()
        with self.assertRaisesRegex(ValueError,"exact fields"):evaluate_study(self.study)
if __name__=="__main__":unittest.main()
