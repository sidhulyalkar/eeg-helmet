"""Sensitivity checks are about a toy mathematical model, not protection."""
import copy
import json
import math
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from neuroshield.models import Parameters
from neuroshield.model_diagnostics import (
    PARAMETERS, METRICS, _cosine, evaluate, main,
)


class ModelDiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = evaluate(scenario="all", preset="default")

    def test_all_four_scenarios_and_five_metric_rows(self):
        self.assertEqual(len(self.result["scenarios"]), 4)
        self.assertEqual(len(self.result["model_observable_rows"]), 20)
        self.assertEqual(len(self.result["model_source_bound_run_fingerprints"]), 4)
        self.assertEqual(len(PARAMETERS), 5)
        self.assertEqual(len(self.result["parameter_pair_pattern_cosines"]), 10)

    def test_s0_and_no_physical_or_health_claim(self):
        result = self.result
        self.assertEqual(result["scientific_evidence_level"], "S0")
        self.assertEqual(result["status"], "SYNTHETIC_LOCAL_SENSITIVITY_ONLY")
        for key in ("measured_data_analyzed", "physical_parameters_identified",
                    "calibration_verified", "physical_model_validation",
                    "safety_or_injury_inference_permitted"):
            self.assertIs(result[key], False)

    def test_peak_proxies_explicitly_not_direct_measurements(self):
        for item in self.result["model_observable_rows"]:
            self.assertFalse(item["directly_comparable_to_physical_3d_measurement"])
            self.assertTrue(item["metric_context"])
        row = next(x for x in self.result["model_observable_rows"]
                   if x["metric"] == "peak_neck_torque_proxy_nm")
        self.assertIn("NOT instrumented upper-neck moment", row["metric_context"])

    def test_all_elasticities_and_step_checks_finite_if_defined(self):
        for row in self.result["model_observable_rows"]:
            self.assertGreaterEqual(row["baseline_absolute_peak"], 0.)
            self.assertEqual(set(row["sensitivities"]), set(PARAMETERS))
            for entry in row["sensitivities"].values():
                if entry["percent_parameter_elasticity"] is not None:
                    self.assertTrue(math.isfinite(entry["percent_parameter_elasticity"]))
                self.assertTrue(math.isfinite(entry["absolute_metric_change_per_unit_parameter_fraction"]))
                self.assertTrue(0 <= entry["fractional_derivative_step_difference"] <= 2.000001)

    def test_source_fingerprints_and_report_hash(self):
        from neuroshield.provenance import canonical_hash
        for item in self.result["model_source_bound_run_fingerprints"]:
            self.assertEqual(len(item["scientific_fingerprint"]), 64)
        content = dict(self.result)
        digest = content.pop("report_sha256")
        self.assertEqual(digest, canonical_hash(content))

    def test_deterministic_smaller_scenario(self):
        a = evaluate(scenario="oblique")
        b = evaluate(scenario="oblique")
        self.assertEqual(a,b)
        self.assertEqual(len(a["model_observable_rows"]), 5)
        self.assertEqual(a["scenarios"], ["oblique"])

    def test_suggested_preset_and_bounded_parameters(self):
        result = evaluate(scenario="facemask", preset="suggested")
        self.assertEqual(result["parameters"], Parameters.suggested().to_dict())
        self.assertEqual(result["preset"], "suggested")
        self.assertEqual(len(result["model_observable_rows"]), 5)

    def test_reject_arbitrary_or_unknown_scenarios(self):
        for scenario in ("fictional-impact", "", None, ["oblique"]):
            with self.subTest(scenario=scenario), self.assertRaises(ValueError):
                evaluate(scenario=scenario)

    def test_reject_arbitrary_presets(self):
        for preset in ("optimized", None, [], "measured"):
            with self.subTest(preset=preset), self.assertRaises(ValueError):
                evaluate(preset=preset)

    def test_parameter_similarity_is_only_heuristic(self):
        for item in self.result["parameter_pair_pattern_cosines"]:
            self.assertEqual(len(item["parameters"]), 2)
            c = item["cosine"]
            if c is not None:
                self.assertLessEqual(abs(c), 1)
            if item["similar_patterns_heuristic"]:
                self.assertGreaterEqual(abs(c), .98)
        self.assertIn("not a statistical identifiability test", self.result["interpretation"])

    def test_cosine_zero_and_clamping(self):
        self.assertIsNone(_cosine([0,0,0],[1,2,3]))
        self.assertIsNone(_cosine([], []))
        self.assertIsNone(_cosine([1], [1,2]))
        self.assertAlmostEqual(_cosine([1,0,0],[-1,0,0]),-1)
        self.assertAlmostEqual(_cosine([1,1,0],[1,1,0]),1)

    def test_zero_baselines_do_not_generate_infinite_elasticity(self):
        def zero(*_, **__):
            return {"metrics_unrounded": {k: 0. for k in METRICS},
                    "metrics": {"mount_limit_engaged": False},
                    "provenance": {"scientific_fingerprint": "0"*64}}
        with patch("neuroshield.model_diagnostics.simulate", side_effect=zero):
            r = evaluate(scenario="facemask")
        self.assertIn("ZERO_BASELINE_METRIC_CANNOT_BE_NORMALIZED", r["warnings"])
        self.assertTrue(all(v["percent_parameter_elasticity"] is None
                            for row in r["model_observable_rows"]
                            for v in row["sensitivities"].values()))

    def test_nonsmooth_peak_derivatives_are_flagged(self):
        nominal = Parameters().mount_k_n_m
        def jump(scene, params):
            val = max(0., params.mount_k_n_m - nominal*1.0075)
            peaks = {k:1. for k in METRICS}
            peaks[METRICS[0]] = val
            return {"metrics_unrounded":peaks, "metrics":{"mount_limit_engaged":False},
                    "provenance":{"scientific_fingerprint":"1"*64}}
        with patch("neuroshield.model_diagnostics.simulate", side_effect=jump):
            r = evaluate(scenario="oblique")
        self.assertIn("LOCAL_PEAK_DERIVATIVE_DEPENDS_ON_STEP", r["warnings"])
        row = r["model_observable_rows"][0]
        self.assertTrue(row["sensitivities"]["mount_k_n_m"]["derivative_stability_warning"])

    def test_nonfinite_solver_output_is_rejected(self):
        def broken(*_,**__):
            return {"metrics_unrounded":{k:float("nan") for k in METRICS},
                    "metrics":{"mount_limit_engaged":False},
                    "provenance":{"scientific_fingerprint":"2"*64}}
        with patch("neuroshield.model_diagnostics.simulate", side_effect=broken):
            with self.assertRaisesRegex(ArithmeticError, "Nonfinite"):
                evaluate(scenario="oblique")

    def test_cli_writes_and_refuses_to_replace_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)/"report.json"
            with redirect_stdout(StringIO()):
                self.assertEqual(main(["--scenario","facemask","--out",str(out)]),0)
            saved = json.loads(out.read_text())
            self.assertEqual(saved["scientific_evidence_level"],"S0")
            with redirect_stdout(StringIO()), self.assertRaises(SystemExit) as caught:
                main(["--scenario","facemask","--out",str(out)])
            self.assertEqual(caught.exception.code,2)
            self.assertEqual(json.loads(out.read_text()),saved)

    def test_no_input_files_and_no_mutation(self):
        current = Parameters()
        copy_of_current = copy.deepcopy(current.to_dict())
        with patch("neuroshield.model_diagnostics.simulate", wraps=__import__(
            "neuroshield.model_diagnostics", fromlist=["simulate"]).simulate) as run:
            r = evaluate(scenario="rear")
        self.assertEqual(current.to_dict(), copy_of_current)
        self.assertEqual(run.call_count, 21)
        self.assertFalse(r["measured_data_analyzed"])


if __name__ == "__main__":
    unittest.main()
