"""Strict S0-only role, units and frame qualification with synthetic demonstrations."""
import csv
import hashlib
import json
import math
import tempfile
import unittest
from pathlib import Path

from neuroshield.measurement_mapping import review_mapping, main, SCHEMA


def h(value):
    return hashlib.sha256(value.encode()).hexdigest()


def fixture(root):
    data_path = root / "toy.csv"
    headers = ["relative_ms", "head_ax_g", "head_ay_g", "head_az_g", "neck_mx_Nmm", "neck_my_Nmm", "neck_mz_Nmm"]
    with data_path.open("w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(headers)
        for i in range(8):
            wr.writerow([i-3, 1., 0., 0., 0., 2000., 0.])
    x = [[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]]
    identity = [[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]]
    def group(q, cols, unit, matrix, frame, point, grav):
        return {"quantity": q, "indices_xyz": cols,
                "header_sha256_xyz": [h(headers[i]) for i in cols],
                "source_unit": unit, "source_frame": "local-sensor-frame",
                "target_frame": frame, "rotation_target_from_source": matrix,
                "measurement_point": point, "target_point": point,
                "calibration_reference": "synthetic-calibration-pending",
                "filter_reference": "synthetic-no-filter",
                "uncertainty_reference": "synthetic-uncertainty-pending",
                "gravity_policy": grav}
    p = {"schema_version": SCHEMA, "source_id_declaration": "synthetic-headform-fixture",
         "origin_declaration": "SYNTHETIC_HEADFORM_FIXTURE",
         "raw_file_sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
         "delimiter": "comma",
         "clock": {"index": 0, "header_sha256": h(headers[0]),
                   "unit": "ms", "time_reference": "relative_trigger"},
         "groups": [group("head_linear_acceleration", [1,2,3], "g", x,
                          "right_handed_headform_body", "sensor-location-01", "removed_with_documentation"),
                    group("upper_neck_moment", [4,5,6], "N*mm", identity,
                          "right_handed_upper_neck_frame", "loadcell-origin-01", "not_applicable")],
         "mapping_status": "proposed_unverified",
         "review_reference": "synthetic-plan-not-reviewed"}
    path = root / "plan.json"
    path.write_text(json.dumps(p))
    return data_path, path, p


class MappingTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name)
        self.data, self.plan, self.p = fixture(self.root)

    def write(self):
        self.plan.write_text(json.dumps(self.p))

    def test_synthetic_rotation_units_and_explicit_frame(self):
        r = review_mapping(self.plan, self.data)
        self.assertEqual(r["status"], "REVIEW_REQUIRED")
        self.assertEqual(r["scientific_evidence_level"], "S0")
        self.assertFalse(r["data_import_authorized"])
        self.assertEqual(r["data_rows"], 8)
        s = r["synthetic_aggregate_demo"]
        self.assertAlmostEqual(s["head_linear_acceleration"]["peak_resultant_si"], 9.80665)
        self.assertAlmostEqual(s["head_linear_acceleration"]["mean_components_target_frame_si"][1], 9.80665)
        self.assertAlmostEqual(s["upper_neck_moment"]["peak_resultant_si"], 2.)
        self.assertEqual(s["upper_neck_moment"]["units"], "N*m")
        self.assertEqual(r["source_identity_verified"], False)

    def test_schema_contract_is_distributable(self):
        from importlib import resources
        s = json.loads(resources.files("neuroshield").joinpath("schemas/measurement-mapping.schema.json").read_text())
        self.assertEqual(s["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(s["properties"]["schema_version"]["const"], SCHEMA)
        self.assertEqual(s["additionalProperties"], False)

    def test_deterministic(self):
        self.assertEqual(review_mapping(self.plan,self.data), review_mapping(self.plan,self.data))

    def test_real_data_is_review_only_even_if_someone_relabels_synthetic(self):
        self.p["origin_declaration"] = "NONHUMAN_INSTRUMENTED_HEADFORM"
        self.write()
        r = review_mapping(self.plan,self.data)
        self.assertIsNone(r["synthetic_aggregate_demo"])
        self.assertFalse(r["mapping_approved"])

    def test_wrong_file_hash_rejected(self):
        self.p["raw_file_sha256"] = "a" * 64
        self.write()
        with self.assertRaisesRegex(ValueError,"Raw file changed"):
            review_mapping(self.plan,self.data)

    def test_wrong_header_hash_rejected(self):
        self.p["groups"][0]["header_sha256_xyz"][0] = "f" * 64
        self.write()
        with self.assertRaisesRegex(ValueError,"Frozen component header"):
            review_mapping(self.plan,self.data)

    def test_mirror_rotation_rejected(self):
        self.p["groups"][0]["rotation_target_from_source"] = [[-1,0,0],[0,1,0],[0,0,1]]
        self.write()
        with self.assertRaisesRegex(ValueError,"handedness"):
            review_mapping(self.plan,self.data)

    def test_skew_rotation_rejected(self):
        self.p["groups"][0]["rotation_target_from_source"] = [[1,0.2,0],[0,1,0],[0,0,1]]
        self.write()
        with self.assertRaisesRegex(ValueError,"orthonormal"):
            review_mapping(self.plan,self.data)

    def test_nan_rotation_rejected(self):
        self.p["groups"][0]["rotation_target_from_source"][0][0] = float("nan")
        self.write()
        with self.assertRaisesRegex(ValueError,"finite"):
            review_mapping(self.plan,self.data)

    def test_target_frame_for_neck_must_not_be_head_frame(self):
        self.p["groups"][1]["target_frame"] = "right_handed_headform_body"
        self.write()
        with self.assertRaisesRegex(ValueError,"frame mismatch"):
            review_mapping(self.plan,self.data)

    def test_unit_for_quantity_must_be_compatible(self):
        self.p["groups"][1]["source_unit"] = "g"
        self.write()
        with self.assertRaisesRegex(ValueError,"unit inconsistent"):
            review_mapping(self.plan,self.data)

    def test_position_change_not_silently_converted(self):
        self.p["groups"][1]["target_point"] = "headform-cog"
        self.write()
        with self.assertRaisesRegex(ValueError,"Reference point change"):
            review_mapping(self.plan,self.data)

    def test_reject_reused_channels(self):
        self.p["groups"][1]["indices_xyz"][1] = 1
        self.write()
        with self.assertRaisesRegex(ValueError,"Duplicate or unavailable"):
            review_mapping(self.plan,self.data)

    def test_reject_human_origin(self):
        self.p["origin_declaration"] = "HUMAN_EEG"
        self.write()
        with self.assertRaisesRegex(ValueError,"Only explicitly declared"):
            review_mapping(self.plan,self.data)

    def test_unknown_evidence_promotion_field_refused(self):
        self.p["scientific_evidence_level"] = "S3"
        self.write()
        with self.assertRaisesRegex(ValueError,"unexpected or missing fields"):
            review_mapping(self.plan,self.data)

    def test_bad_clock_gap_refused(self):
        with self.data.open("w", newline="") as f:
            w=csv.writer(f)
            w.writerow(["relative_ms","head_ax_g","head_ay_g","head_az_g","neck_mx_Nmm","neck_my_Nmm","neck_mz_Nmm"])
            for i in [0, 1, 2, 3, 4, 100, 101, 102]:
                w.writerow([i,1.,0.,0.,0.,2000.,0.])
        self.p["raw_file_sha256"] = hashlib.sha256(self.data.read_bytes()).hexdigest()
        self.write()
        with self.assertRaisesRegex(ValueError,"Sample clock not structurally qualified"):
            review_mapping(self.plan,self.data)

    def test_duplicate_json_fields_rejected(self):
        self.plan.write_text('{"schema_version":"x","schema_version":"y"}')
        with self.assertRaisesRegex(ValueError,"Duplicate mapping JSON key"):
            review_mapping(self.plan,self.data)

    def test_symlink_plan_rejected(self):
        other = self.root / "link.json"
        try: other.symlink_to(self.plan)
        except (OSError, NotImplementedError): self.skipTest("No symlink support")
        with self.assertRaisesRegex(ValueError,"regular mapping plan"):
            review_mapping(other,self.data)

    def test_cli_preserves_existing_reports(self):
        report = self.root / "output.json"
        report.write_text("preserve")
        with self.assertRaises(SystemExit) as e:
            main([str(self.plan),str(self.data),"--out",str(report)])
        self.assertEqual(e.exception.code, 2)
        self.assertEqual(report.read_text(),"preserve")

    def test_no_raw_samples_or_private_paths_leak(self):
        r = review_mapping(self.plan,self.data)
        s = json.dumps(r)
        self.assertNotIn(str(self.data),s)
        self.assertNotIn("head_ax_g",s)
        self.assertNotIn('"samples"',s)


if __name__ == "__main__": unittest.main()
