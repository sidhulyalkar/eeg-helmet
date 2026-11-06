"""Independent syntactic/geometry checks for a deliberately nonwearable S0 concept."""
from __future__ import annotations

import copy
from contextlib import redirect_stdout
from hashlib import sha256
from io import StringIO
import json
import math
from pathlib import Path
import tempfile
import unittest

from neuroshield import headform_concept as concept


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "headform-sites-SYNTHETIC.json"


class SyntheticHeadformTests(unittest.TestCase):
    def setUp(self):
        self.obj = concept.load_manifest(FIXTURE)
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.source = self.root / "manifest.json"
        self._write()

    def _write(self):
        self.source.write_text(json.dumps(self.obj, allow_nan=True) + "\n", encoding="utf-8")

    def invalid(self):
        self._write()
        with self.assertRaises(concept.HeadformConceptError):
            concept.load_manifest(self.source)

    def test_fixture_is_nine_symbolic_points_only(self):
        points, spacing = concept.validate(self.obj)
        self.assertEqual(len(points), 9)
        self.assertGreater(spacing, 8)
        self.assertEqual(points[0], [0.0, 0.0, 110.0])
        self.assertEqual(self.obj["origin"], concept.ORIGIN)
        self.assertEqual(self.obj["claim"], concept.LIMITATION)
        self.assertTrue(all(p["id"].startswith("SITE-") for p in self.obj["sites"]))

    def test_deterministic_render_and_strict_nonhuman_receipt(self):
        a = concept.render_scad(self.obj)
        self.assertEqual(a, concept.render_scad(self.obj))
        self.assertIn("NON-INSTALLABLE", a)
        self.assertIn("NOT 10-20 scalp locations", a)
        self.assertIn("NO WEARABLE", a)
        report = concept.receipt(self.obj, a)
        self.assertEqual(report, concept.receipt(self.obj, a))
        self.assertEqual(report["scad_sha256"], sha256(a.encode()).hexdigest())
        self.assertEqual(report["site_count"], 9)
        self.assertEqual(report["headform_bounds_mm"], [170, 190, 220])
        self.assertEqual(report["evidence_tier"], "S0")
        for key in ("electrode_montage_validated", "physical_fabrication_authorized",
                    "independent_hardware_validation", "human_data_processed"):
            self.assertIs(report[key], False)

    def test_export_creates_source_and_receipt_and_refuses_overwrite(self):
        output = self.root / "preview.scad"
        receipt = self.root / "receipt.json"
        report = concept.write_concept(self.source, output, receipt)
        self.assertTrue(output.is_file())
        self.assertEqual(json.loads(receipt.read_text()), report)
        self.assertEqual(sha256(output.read_bytes()).hexdigest(), report["scad_sha256"])
        before = (output.read_bytes(), receipt.read_bytes())
        with self.assertRaises(concept.HeadformConceptError):
            concept.write_concept(self.source, output, self.root / "other.json")
        self.assertFalse((self.root / "other.json").exists())
        with self.assertRaises(concept.HeadformConceptError):
            concept.write_concept(self.source, self.root / "other.scad", receipt)
        self.assertFalse((self.root / "other.scad").exists())
        self.assertEqual(before, (output.read_bytes(), receipt.read_bytes()))

    def test_reject_ambiguous_context_and_unauthorized_keys(self):
        for field, value in (("origin", "HUMAN_EEG"), ("claim", "CERTIFIED_HELMET"),
                             ("units", "m"), ("frame", "unknown"), ("schema", "fake"),
                             ("design_id", "x")):
            with self.subTest(field=field):
                self.obj = concept.load_manifest(FIXTURE)
                self.obj[field] = value
                self.invalid()
        self.obj = concept.load_manifest(FIXTURE)
        self.obj["participant_scan_path"] = "private.dcm"
        self.invalid()

    def test_reject_malformed_geometry(self):
        for bad in ([False, 95, 110], [float("nan"), 95, 110], [0, 95, 110],
                    [85, 950, 110], [85, 95], ["85", 95, 110]):
            with self.subTest(bad=bad):
                self.obj = concept.load_manifest(FIXTURE)
                self.obj["headform_radii_mm"] = bad
                self.invalid()
        for bad in ([0, 0, 0], [1, 1, 1], [True, 0, 0], [math.inf, 0, 0],
                    [0, 0], [0, 0, "1"]):
            with self.subTest(bad=bad):
                self.obj = concept.load_manifest(FIXTURE)
                self.obj["sites"][0]["direction_unit"] = bad
                self.invalid()

    def test_reject_duplicate_and_overlapping_sites(self):
        self.obj["sites"][1]["id"] = self.obj["sites"][0]["id"]
        self.invalid()
        self.obj = concept.load_manifest(FIXTURE)
        self.obj["sites"][1]["direction_unit"] = self.obj["sites"][0]["direction_unit"]
        self.invalid()
        self.obj = concept.load_manifest(FIXTURE)
        self.obj["sites"][0]["electrode_voltage"] = 0.001
        self.invalid()

    def test_reject_duplicate_json_keys_and_nonfinite_literals(self):
        raw = self.source.read_text("utf-8").replace('"origin":', '"origin": "HUMAN", "origin":', 1)
        self.source.write_text(raw, encoding="utf-8")
        with self.assertRaises(concept.HeadformConceptError):
            concept.load_manifest(self.source)
        self.source.write_text(self.source.read_text().replace('"headform_radii_mm": [85, 95, 110]',
                                                                  '"headform_radii_mm": [NaN, 95, 110]'))
        with self.assertRaises(concept.HeadformConceptError):
            concept.load_manifest(self.source)

    def test_reject_symlink_source_and_existing_outputs(self):
        alias = self.root / "alias.json"
        try:
            alias.symlink_to(self.source)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks unavailable")
        with self.assertRaises(concept.HeadformConceptError):
            concept.load_manifest(alias)
        with self.assertRaises(concept.HeadformConceptError):
            concept.write_concept(self.source, self.source, self.root / "new.json")

    def test_cli_prints_non-authorizing_receipt(self):
        output = StringIO()
        with redirect_stdout(output):
            code = concept.main([str(self.source), "--out", str(self.root / "preview.scad"),
                                 "--receipt", str(self.root / "receipt.json")])
        self.assertEqual(code, 0)
        report = json.loads(output.getvalue())
        self.assertFalse(report["physical_fabrication_authorized"])
        self.assertEqual(report["origin"], concept.ORIGIN)


if __name__ == "__main__":
    unittest.main()
