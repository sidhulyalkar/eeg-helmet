"""Independent analytic and adversarial tests for S0 nonhuman 3D frame mapping."""
import copy
import json
import math
import tempfile
import unittest
from pathlib import Path

from neuroshield.frame_projection import (SCHEMA, evaluate, project_sample, validate_plan)
from neuroshield.provenance import canonical_hash

ROOT=Path(__file__).resolve().parents[1]


def plan():
    return {
        "schema_version":SCHEMA,"scope":"NONHUMAN_HEADFORM_ONLY",
        "source_frame":"right_handed_headform_body","target_frame":"rigid_headform_target",
        "source_to_target_rotation":[[1,0,0],[0,1,0],[0,0,1]],
        "sensor_to_target_m":[0.0,0.0,0.0],
        "projection_axis_target":[1.0,0.0,0.0],
        "input_acceleration_semantics":"GRAVITY_REMOVED_LINEAR_ACCELERATION",
        "window_s":[0,0.025],"registration_reference":"SYNTHETIC_NOT_INDEPENDENTLY_REGISTERED"}


class GeometryTests(unittest.TestCase):
    def test_identity_and_signed_projection(self):
        r,offset,axis,*_=validate_plan(plan())
        self.assertEqual(project_sample((5,6,7),(8,9,10),(11,12,13),r,offset,axis),(5.,8.,11.))
        self.assertEqual(project_sample((-5,0,0),(0,0,0),(0,0,0),r,offset,axis)[0],-5)

    def test_tangential_acceleration_analytic(self):
        p=plan();p["sensor_to_target_m"]=[0.0,0.1,0.0]
        r,offset,axis,*_=validate_plan(p)
        v=project_sample((0,0,0),(0,0,100),(0,0,0),r,offset,axis)
        self.assertAlmostEqual(v[0],-10.)
        self.assertAlmostEqual(v[1],0.)

    def test_centripetal_acceleration_analytic(self):
        p=plan();p["sensor_to_target_m"]=[.25,0,0]
        r,offset,axis,*_=validate_plan(p)
        v=project_sample((0,0,0),(0,0,0),(0,0,4),r,offset,axis)
        self.assertAlmostEqual(v[0],-4.0)

    def test_proper_rotation_y_axis(self):
        p=plan();p["source_to_target_rotation"]=[[0,-1,0],[1,0,0],[0,0,1]]
        p["projection_axis_target"]=[0,1,0]
        r,offset,axis,*_=validate_plan(p)
        self.assertEqual(project_sample((3,0,0),(7,0,0),(9,0,0),r,offset,axis),(3,7,9))

    def test_reflection_and_shear_rejected(self):
        p=plan();p["source_to_target_rotation"]=[[-1,0,0],[0,1,0],[0,0,1]]
        with self.assertRaisesRegex(ValueError,"right-handed"):validate_plan(p)
        p["source_to_target_rotation"]=[[1,.1,0],[0,1,0],[0,0,1]]
        with self.assertRaisesRegex(ValueError,"orthonormal"):validate_plan(p)

    def test_nonunit_axis_wrong_units_and_long_offset_rejected(self):
        for key,value in [("projection_axis_target",[0.5,0,0]),
                          ("input_acceleration_semantics","RAW_ACCELEROMETER_SPECIFIC_FORCE"),
                          ("sensor_to_target_m",[.51,0,0]),
                          ("window_s",[.025,.025]),
                          ("source_frame","sensor_unknown")]:
            with self.subTest(key=key):
                p=plan();p[key]=value
                with self.assertRaises(ValueError):validate_plan(p)

    def test_boolean_nan_unknown_fields_are_rejected(self):
        for key,value in [("projection_axis_target",[True,0,0]),
                          ("projection_axis_target",[float('nan'),0,0])]:
            p=plan();p[key]=value
            with self.assertRaises(ValueError):validate_plan(p)
        p=plan();p["athlete_id"]="PRIVATE"
        with self.assertRaises(ValueError):validate_plan(p)


class FileTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.plan_path=self.root/"plan.json"
        self.write_plan(plan())
        self.profile=ROOT/"examples"/"bench-reference-SYNTHETIC-profile.json"
        self.manifest=ROOT/"examples"/"bench-reference-SYNTHETIC-manifest.json"
        self.csv=ROOT/"examples"/"bench-reference-SYNTHETIC.csv"

    def write_plan(self,doc):
        self.plan_path.write_text(json.dumps(doc))

    def run_eval(self, fingerprint=None):
        return evaluate(self.plan_path,self.profile,self.manifest,self.csv,
                        expected_plan_sha256=fingerprint or canonical_hash(plan()))

    def test_demo_is_repeatable_and_never_claims_validation(self):
        a=self.run_eval()
        self.assertEqual(a,self.run_eval())
        self.assertEqual(a["scientific_evidence_level"],"S0")
        self.assertEqual(a["status"],"SYNTHETIC_GEOMETRY_ONLY")
        self.assertEqual(a["sample_count"],51)
        self.assertIn("NO_VALIDATED_1D_MODEL_CORRESPONDENCE",a["blockers"])
        self.assertNotIn("samples",a)
        self.assertNotIn("traces",a)
        self.assertNotIn(str(self.root),json.dumps(a))
        self.assertEqual(len(a["acquisition_identity_sha256"]),64)

    def test_posthoc_edit_breaks_plan_lock(self):
        modified=plan();modified["projection_axis_target"]=[0,1,0]
        self.write_plan(modified)
        with self.assertRaisesRegex(ValueError,"pinned"):
            self.run_eval()

    def test_invalid_pinned_sha_rejected(self):
        with self.assertRaisesRegex(ValueError,"SHA-256"):
            self.run_eval("xyz")

    def test_incomplete_window_rejected(self):
        p=plan();p["window_s"]=[0,.05];self.write_plan(p)
        with self.assertRaisesRegex(ValueError,"not fully covered"):
            self.run_eval(canonical_hash(p))

    def test_wrong_gravity_semantics_rejected_even_with_matching_sha(self):
        p=plan();p["input_acceleration_semantics"]="UNKNOWN";self.write_plan(p)
        with self.assertRaisesRegex(ValueError,"gravity compensated"):
            self.run_eval(canonical_hash(p))

    def test_validation_rejects_human_origin(self):
        m=json.loads(self.manifest.read_text());m["origin"]="HUMAN_PLAYER"
        path=self.root/"bad-manifest.json";path.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError,"human"):
            evaluate(self.plan_path,self.profile,path,self.csv,expected_plan_sha256=canonical_hash(plan()))

if __name__=="__main__":unittest.main()
