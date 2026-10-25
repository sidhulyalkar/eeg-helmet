import copy
import unittest
from neuroshield.external_evidence import SCHEMA, review_record

def fixture():
    return {"schema_version":SCHEMA,"dataset_id":"synthetic-demo","origin":"SYNTHETIC_HEADFORM_FIXTURE",
        "source":{"url":"synthetic:fixture","sha256":"a"*64,"license_document":"internal","citation":"test fixture"},
        "rights":{"local_analysis_approved":False,"redistribution_approved":False,"reviewer_reference":"not reviewed"},
        "acquisition":{"calibration_reviewed":False,"coordinate_frame_reviewed":False,"uncertainty_reviewed":False,"laboratory_reference":"none"},
        "evaluation":{"preregistration_reference":"demo","metrics":["linear_peak_m_s2","angular_peak_rad_s2"],"replicate_count":1,"independent_lab_reviewed":False}}

class EvidenceTests(unittest.TestCase):
    def test_synthetic_is_blocked(self):
        r=review_record(fixture())
        self.assertEqual(r["status"],"BLOCKED")
        self.assertIn("SYNTHETIC_ONLY",r["blockers"])
    def test_no_human_origin(self):
        f=fixture();f["origin"]="HUMAN_EEG"
        with self.assertRaises(ValueError): review_record(f)
    def test_reject_extra_data(self):
        f=fixture();f["athlete"]="private"
        with self.assertRaises(ValueError): review_record(f)
    def test_invalid_hash(self):
        f=fixture();f["source"]["sha256"]="Z"*64
        with self.assertRaises(ValueError): review_record(f)
    def test_unknown_metrics(self):
        f=fixture();f["evaluation"]["metrics"]=["concussion_risk"]
        with self.assertRaises(ValueError): review_record(f)
    def test_determinism(self):
        self.assertEqual(review_record(fixture())["record_sha256"],review_record(copy.deepcopy(fixture()))["record_sha256"])
    def test_review_attestation_cannot_promote(self):
        f=fixture();f["origin"]="NONHUMAN_INSTRUMENTED_HEADFORM";f["source"]["url"]="https://example.org/data"
        f["rights"]["local_analysis_approved"]=True
        for k in ("calibration_reviewed","coordinate_frame_reviewed","uncertainty_reviewed"):f["acquisition"][k]=True
        f["evaluation"]["replicate_count"]=3;f["evaluation"]["independent_lab_reviewed"]=True
        r=review_record(f)
        self.assertEqual((r["status"],r["scientific_evidence_level"]),("REVIEW_REQUIRED","S0"))
    def test_requires_https_for_external(self):
        f=fixture();f["origin"]="NONHUMAN_INSTRUMENTED_HEADFORM"
        with self.assertRaises(ValueError):review_record(f)
    def test_bool_is_not_integer(self):
        f=fixture();f["rights"]["local_analysis_approved"]=1
        with self.assertRaises(ValueError):review_record(f)
if __name__=="__main__":unittest.main()
