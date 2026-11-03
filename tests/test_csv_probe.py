"""Local CSV inspection must not invent a source-specific mapping or safety claim."""
from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from neuroshield.csv_probe import inspect_csv, main


class CsvProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "synthetic-provider-shape.csv"
        with self.path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Time (ms)", "Unknown head channel", "Upper neck moment (unverified)"])
            w.writerows([[i, i * 2, i * 0.25] for i in range(12)])

    def inspect(self, **kwargs):
        return inspect_csv(self.path, source_id="borealis-escooter-headneck-2024",
                           origin="SYNTHETIC_HEADFORM_FIXTURE", **kwargs)

    def test_default_is_unmapped_and_never_measured_evidence(self):
        result = self.inspect()
        self.assertEqual(result["status"], "STRUCTURAL_REVIEW_REQUIRED")
        self.assertEqual(result["scientific_evidence_level"], "S0")
        self.assertEqual(result["data_rows"], 12)
        self.assertFalse(result["data_import_authorized"])
        self.assertNotIn("header_label_local_opt_in", result["columns"][0])
        self.assertEqual(result["timebase"]["status"], "NOT_CHECKED_NO_EXPLICIT_MAPPING")

    def test_explicit_millisecond_clock(self):
        a = self.inspect(time_column=0, time_unit="ms")
        self.assertEqual(a["timebase"]["status"], "STRUCTURE_ONLY")
        self.assertAlmostEqual(a["timebase"]["estimated_sampling_hz"], 1000)
        self.assertEqual(a["timebase"]["possible_missing_sample_gaps"], 0)
        self.assertEqual(a["structural_flags"], [])

    def test_header_opt_in_still_no_sample_values(self):
        a = self.inspect(include_header_labels=True)
        self.assertEqual(a["columns"][1]["header_label_local_opt_in"], "Unknown head channel")
        self.assertNotIn("samples", a)
        self.assertFalse(a["calibration_verified"])

    def test_reject_unknown_data_class(self):
        with self.assertRaisesRegex(ValueError, "nonhuman"):
            inspect_csv(self.path, source_id="borealis-escooter-headneck-2024", origin="HUMAN_RECORDING")

    def test_reject_bad_time_params(self):
        for opts in ({"time_column": 0}, {"time_unit": "ms"},
                     {"time_column": 99, "time_unit": "s"},
                     {"time_column": True, "time_unit": "s"}):
            with self.subTest(opts=opts), self.assertRaises(ValueError):
                self.inspect(**opts)

    def test_reject_nonmonotonic_timestamp(self):
        with self.path.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([3, 0, 0])
        with self.assertRaisesRegex(ValueError, "increasing"):
            self.inspect(time_column=0, time_unit="ms")

    def test_negative_pretrigger_times_are_valid(self):
        with self.path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["relative_time_ms", "headform_a"])
            w.writerows([[x, 1.0] for x in (-3, -2, -1, 0, 1, 2)])
        report = self.inspect(time_column=0, time_unit="ms")
        self.assertEqual(report["timebase"]["status"], "STRUCTURE_ONLY")
        self.assertAlmostEqual(report["timebase"]["first_time_s"], -.003)

    def test_reject_nan_timestamp(self):
        with self.path.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["NaN", 0, 0])
        with self.assertRaisesRegex(ValueError, "finite"):
            self.inspect(time_column=0, time_unit="ms")

    def test_sample_gap_is_flagged_not_interpolated(self):
        with self.path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["time", "ax"])
            w.writerows([[x, 2*x] for x in (0,1,2,3,4,50,51,52)])
        a = self.inspect(time_column=0, time_unit="ms")
        self.assertGreater(a["timebase"]["possible_missing_sample_gaps"], 0)
        self.assertIn("REVIEW_SAMPLE_CLOCK_GAPS_OR_JITTER", a["structural_flags"])

    def test_reject_duplicate_headers(self):
        self.path.write_text("a,a\n0,1\n1,2\n2,3\n")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.inspect()

    def test_reject_invalid_row_width(self):
        self.path.write_text("x,y\n0,1\n1,2,3\n2,4\n")
        with self.assertRaisesRegex(ValueError, "field count"):
            self.inspect()

    def test_symlink_rejected(self):
        alias = Path(self.tmp.name) / "link.csv"
        try:
            alias.symlink_to(self.path)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks unavailable")
        with self.assertRaisesRegex(ValueError, "nonsymlink"):
            inspect_csv(alias, source_id="borealis-escooter-headneck-2024",
                        origin="SYNTHETIC_HEADFORM_FIXTURE")

    def test_cli_does_not_overwrite_existing_output(self):
        out = Path(self.tmp.name) / "report.json"
        out.write_text("preserve")
        with self.assertRaises(SystemExit) as ctx:
            main([str(self.path), "--source-id", "borealis-escooter-headneck-2024",
                  "--origin", "SYNTHETIC_HEADFORM_FIXTURE", "--out", str(out)])
        self.assertEqual(ctx.exception.code, 2)
        self.assertEqual(out.read_text(), "preserve")

    def test_deterministic_report_for_unchanged_file(self):
        self.assertEqual(self.inspect(), self.inspect())
        self.assertEqual(len(self.inspect()["raw_file_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
