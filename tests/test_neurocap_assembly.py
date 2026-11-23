"""S0 NeuroCap visual-geometry regression checks; no human recordings or devices."""
from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "cad" / "neurocap"
SPEC = importlib.util.spec_from_file_location("neurocap_assembly", LAB / "build.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class NeurocapHeadformConceptTests(unittest.TestCase):
    def setUp(self):
        self.data = module.load_manifest(LAB / "manifest.json")

    def test_declared_components_site_count_and_scientific_ceiling(self):
        self.assertEqual(self.data["status"], "UNVALIDATED_NONWEARABLE_CONCEPT")
        self.assertEqual(self.data["evidence_tier"], "S0")
        self.assertEqual(self.data["units"], "mm")
        self.assertEqual(len(self.data["components"]), 7)
        self.assertEqual(len(self.data["scalp_sites"]), 6)
        self.assertEqual(len(self.data["ear_sites"]), 2)
        self.assertEqual(self.data["electrical_contract"]["amplifier_reference"], "UNSPECIFIED")
        self.assertEqual(self.data["electrical_contract"]["skin_connection"], "PROHIBITED_IN_THIS_CONCEPT")

    def test_export_is_deterministic_and_receipt_is_not_qualification(self):
        with tempfile.TemporaryDirectory() as work:
            p = Path(work)
            a = module.build(LAB / "manifest.json", p / "a.scad", p / "a.json")
            b = module.build(LAB / "manifest.json", p / "b.scad", p / "b.json")
            self.assertEqual(a, b)
            self.assertEqual((p / "a.scad").read_bytes(), (p / "b.scad").read_bytes())
            self.assertEqual(len(a["source_sha256"]), 64)
            self.assertEqual(len(a["scad_sha256"]), 64)
            self.assertEqual(a["site_count"], 8)
            self.assertFalse(a["human_anatomy_measured"])
            self.assertFalse(a["skin_contact_authorized"])
            self.assertFalse(a["protective_use_authorized"])
            source = (p / "a.scad").read_text()
            for part in ("headform", "crown_and_brim", "frame_study", "scalp_placeholders", "ear_placeholders", "signal_paths", "pod_placeholder"):
                self.assertIn(f"module {part}()", source)

    def test_geometry_parameter_changes_shape_but_not_evidence(self):
        a = module.generate_scad(copy.deepcopy(self.data))
        changed = copy.deepcopy(self.data)
        changed["geometry"]["ear_y_radius_mm"] = 25
        b = module.generate_scad(changed)
        self.assertNotEqual(a, b)
        self.assertIn("NONWEARABLE", a)
        self.assertIn("NONWEARABLE", b)

    def test_bad_units_status_and_frame_are_rejected(self):
        for path, value in [
            (("units",), "cm"),
            (("status",), "HUMAN_READY"),
            (("origin",), "HUMAN_SCAN"),
            (("coordinate_frame", "z"), "+inferior"),
        ]:
            data = copy.deepcopy(self.data)
            target = data
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            with self.subTest(path=path), self.assertRaises(ValueError):
                module.validate_manifest(data)

    def test_bad_geometry_and_bad_site_claims_are_rejected(self):
        for key, value in [
            ("radii_mm", [80, 0, 112]),
            ("cap_shell_gap_mm", float("nan")),
            ("rib_half_span_mm", 74),
            ("ear_center_x_mm", 50),
        ]:
            data = copy.deepcopy(self.data)
            data["geometry"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                module.validate_manifest(data)
        for mutator in [
            lambda x: x["scalp_sites"][1].update(id="FL"),
            lambda x: x["scalp_sites"][0].update(status="MEASURED"),
            lambda x: x["ear_sites"][1].update(side=-1),
            lambda x: x["electrical_contract"].update(skin_connection="PERMITTED"),
            lambda x: x["components"][0].update(qualification="VALIDATED"),
        ]:
            data = copy.deepcopy(self.data)
            mutator(data)
            with self.assertRaises(ValueError):
                module.validate_manifest(data)

    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as work:
            path = Path(work) / "bad.json"
            path.write_text('{"origin":"SYNTHETIC_NONHUMAN_HEADFORM","origin":"HUMAN_SCAN"}')
            with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
                module.load_manifest(path)

    def test_preview_is_offline_and_data_bound(self):
        source = (LAB / "index.html").read_text(encoding="utf-8")
        self.assertIn('fetch("manifest.json")', source)
        self.assertIn("UNVALIDATED_NONWEARABLE_CONCEPT", source)
        self.assertIn("pointermove", source)
        self.assertNotIn("cdn.jsdelivr", source.lower())
        self.assertNotIn("threejs.org", source.lower())


if __name__ == "__main__":
    unittest.main()
