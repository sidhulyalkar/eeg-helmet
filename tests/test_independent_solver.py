"""Independent solver qualification: synthetic mathematical tests only."""
import json
import math
import unittest
from neuroshield.independent_solver import rk4_step, solve_reference
from neuroshield.independent_qualification import qualify_independent, judge_case, relative_error
from neuroshield.models import Parameters, SCENARIOS


class AnalyticIntegratorTests(unittest.TestCase):
    def test_undamped_harmonic_oscillator_against_closed_form(self):
        frequency = 20.0
        def rhs(_, y):
            return (y[1], -frequency**2 * y[0])
        t, step = 0.0, 0.0005
        state = (1.0, 0.0)
        for _ in range(1000):
            state = rk4_step(rhs, t, state, step)
            t += step
        self.assertAlmostEqual(state[0], math.cos(frequency*t), delta=1e-7)
        self.assertAlmostEqual(state[1], -frequency*math.sin(frequency*t), delta=1e-6)
        self.assertAlmostEqual((state[1]**2+frequency**2*state[0]**2)/(frequency**2), 1, delta=1e-7)

    def test_reference_energy_balance_and_positive_dissipation(self):
        for scenario in SCENARIOS:
            for p in (Parameters(), Parameters.suggested()):
                with self.subTest(scene=scenario, parameters=p):
                    out = solve_reference(scenario, p)
                    b = out["energy_budget_j"]
                    self.assertGreater(b["external_work"], 0)
                    self.assertGreater(b["damping_dissipation"], 0)
                    self.assertGreaterEqual(b["final_stored"], 0)
                    self.assertAlmostEqual(
                        b["final_stored"]-b["initial_stored"]+b["damping_dissipation"],
                        b["external_work"],delta=max(0.0001,.001*b["external_work"]))
                    self.assertEqual(out["model_evidence_level"],"S0_UNVALIDATED_MECHANICS")

    def test_reference_step_refinement(self):
        a = solve_reference("oblique", dt=.00025)
        b = solve_reference("oblique", dt=.000125)
        for key in a["metrics"]:
            self.assertLess(relative_error(a["metrics"][key], b["metrics"][key]),.01)

    def test_invalid_inputs(self):
        for dt in (0, .002, .0003, float("nan"), True):
            with self.subTest(dt=dt),self.assertRaises(ValueError):
                solve_reference(dt=dt)
        with self.assertRaises(ValueError):solve_reference("unknown")


class NumericalGateTests(unittest.TestCase):
    def test_entire_matrix_passes_reproducibly(self):
        one = qualify_independent()
        two = qualify_independent()
        self.assertEqual(one,two)
        self.assertEqual(one["case_count"],16)
        self.assertEqual(one["passed"],16)
        self.assertEqual(one["status"],"PASS_NUMERICAL_ONLY")
        self.assertEqual(len(one["report_sha256"]),64)
        self.assertEqual(len(one["source_sha256"]["primary_physics"]),64)
        self.assertEqual(len(one["source_sha256"]["reference_solver"]),64)
        self.assertLess(max(c["energy_balance_fraction"] for c in one["cases"]),.005)
        self.assertTrue(all(math.isfinite(c["worst_cross_solver_fraction"]) for c in one["cases"]))
        self.assertTrue(all(c["status"].endswith("NUMERICAL_ONLY") for c in one["cases"]))
        self.assertNotIn("clinical",one["status"].lower())
        self.assertIn("unvalidated", one["evidence_level"].lower())

    def test_case_failure_is_never_silently_suppressed(self):
        good = {"worst_cross_solver_fraction":.01,"worst_reference_refinement_fraction":.001,
                "energy_balance_fraction":.0001}
        self.assertEqual(judge_case(good,solver_tol=.05,refine_tol=.01,balance_tol=.005),(True,[]))
        for field,expected in (("worst_cross_solver_fraction","cross_solver_disagreement"),
                               ("worst_reference_refinement_fraction","reference_not_converged"),
                               ("energy_balance_fraction","energy_balance_not_closed")):
            bad = dict(good,**{field:.5})
            result,failures = judge_case(bad,solver_tol=.05,refine_tol=.01,balance_tol=.005)
            self.assertFalse(result)
            self.assertIn(expected,failures)
        tight = qualify_independent("oblique",solver_tol=1e-6,refine_tol=1e-6,balance_tol=1e-6)
        self.assertEqual(tight["status"],"FAIL_NUMERICAL")

    def test_strict_validation(self):
        for invalid in (0, -.1, 1, float("nan"), True):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                qualify_independent("oblique",solver_tol=invalid)
        with self.assertRaises(ValueError):qualify_independent("bad")


if __name__ == "__main__":
    unittest.main()
