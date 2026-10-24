"""Independent mathematical and regression checks for the optional lab."""
import json
import math
import unittest

try:
    import numpy as np
except ImportError:
    np = None


@unittest.skipUnless(np is not None, "Install neurospatial extra: pip install -e '.[neurospatial]'")
class NeuroSpatialTests(unittest.TestCase):
    def test_reference_removes_one_redundant_channel_and_preserves_differences(self):
        from neuroshield.neurospatial.inverse import independent_reference
        physical = np.array([[1., 2.], [2., 3.], [4., 2.]])
        np.testing.assert_allclose(independent_reference(physical), physical[:2] - physical[-1])
        with self.assertRaises(ValueError):
            independent_reference(physical, 9)

    def test_reference_noise_covariance_keeps_reference_correlation(self):
        from neuroshield.neurospatial.inverse import reference_noise_covariance
        np.testing.assert_allclose(reference_noise_covariance(3, .1), [[.02, .01], [.01, .02]])

    def test_nullspace_is_invisible_and_has_unit_norm(self):
        from neuroshield.neurospatial.inverse import nullspace_ambiguity
        leadfield = np.array([[1., 1., 0.], [0., 1., 1.]])
        z, residual = nullspace_ambiguity(leadfield)
        self.assertAlmostEqual(np.linalg.norm(z), 1., places=12)
        self.assertLess(residual, 1e-12)
        np.testing.assert_allclose(leadfield @ (np.array([2., 0., 1.]) + 9*z), [2., 1.], atol=1e-12)

    def test_posterior_matches_scalar_analytic_case(self):
        from neuroshield.neurospatial.inverse import gaussian_posterior
        post = gaussian_posterior([2.], [[1.]], [[4.]], [[1.]])
        self.assertAlmostEqual(post.mean[0], 1.6)
        self.assertAlmostEqual(post.covariance[0, 0], .8)
        self.assertAlmostEqual(post.resolution[0, 0], .8)
        self.assertAlmostEqual(post.predicted_sensors[0], 1.6)

    def test_fail_closed_bad_matrices(self):
        from neuroshield.neurospatial.inverse import gaussian_posterior
        L = np.array([[1., 0.]])
        for wrong_q in ([[1., 2.], [0., 1.]], [[1., 0.], [0., -1.]], [[math.nan, 0.], [0., 1.]]):
            with self.subTest(wrong_q=wrong_q), self.assertRaises(ValueError):
                gaussian_posterior([1.], L, wrong_q, [[1.]])
        for wrong_g in ([[0.]], [[float('nan')]]):
            with self.assertRaises(ValueError):
                gaussian_posterior([1.], L, np.eye(2), wrong_g)

    def test_known_linear_dynamics_can_increase_observability(self):
        from neuroshield.neurospatial.inverse import observability_rank
        L = [[1., 0.]]
        A = [[1., 1.], [0., 1.]]
        self.assertEqual(observability_rank(L, A, 1), 1)
        self.assertEqual(observability_rank(L, A, 2), 2)
        self.assertEqual(observability_rank(L, np.eye(2), 6), 1)

    def test_toy_report_deterministic_and_honest(self):
        from neuroshield.neurospatial.experiment import run_toy_experiment
        a = run_toy_experiment()
        self.assertEqual(a, run_toy_experiment())
        self.assertNotEqual(a['report_sha256'], run_toy_experiment(seed=77)['report_sha256'])
        self.assertEqual(a['origin'], 'SYNTHETIC')
        self.assertEqual(a['evidence_level'], 'S0')
        self.assertLessEqual(a['leadfield_rank'], a['independent_referenced_measurements'])
        self.assertLess(a['nullspace_residual_l2'], 1e-10)
        self.assertTrue(math.isfinite(a['source_relative_l2_error']))
        self.assertTrue(math.isfinite(a['measured_relative_l2_residual']))
        json.dumps(a, allow_nan=False)

    def test_dimensions_rejected(self):
        from neuroshield.neurospatial.experiment import run_toy_experiment
        for kw in ({'channels':3}, {'channels':40, 'sources':24}, {'seed':True}, {'sources':1025}):
            with self.subTest(kw=kw), self.assertRaises(ValueError):
                run_toy_experiment(**kw)


if __name__ == '__main__':
    unittest.main()
