"""Numerically explicit linear EEG inverse-problem baselines.

L maps N source amplitudes to M independent referenced sensor voltages.
The sensor reference, units, noise covariance, and source prior must be
consistent. These generic operators are NOT a validated head forward model.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Posterior:
    mean: np.ndarray
    covariance: np.ndarray
    resolution: np.ndarray
    predicted_sensors: np.ndarray


def _matrix(value: np.ndarray, label: str) -> np.ndarray:
    out = np.asarray(value, dtype=float)
    if out.ndim != 2 or min(out.shape) < 1 or not np.isfinite(out).all():
        raise ValueError(f"{label} must be a nonempty finite 2-D matrix")
    return out


def _positive_definite(value: np.ndarray, n: int, label: str) -> np.ndarray:
    out = _matrix(value, label)
    if out.shape != (n, n) or not np.allclose(out, out.T, rtol=1e-10, atol=1e-12):
        raise ValueError(f"{label} must be a symmetric {n}x{n} matrix")
    try:
        np.linalg.cholesky(out)
    except np.linalg.LinAlgError as exc:
        raise ValueError(f"{label} must be positive definite") from exc
    return out


def independent_reference(leadfield: np.ndarray, reference_index: int = -1) -> np.ndarray:
    """Difference each other physical electrode against a single reference.

    Drops the redundant reference row to avoid a singular average-reference
    covariance. Measurement noise becomes correlated after referencing.
    """
    physical = _matrix(leadfield, "physical leadfield")
    if physical.shape[0] < 2:
        raise ValueError("at least two physical electrodes required")
    if not -physical.shape[0] <= reference_index < physical.shape[0]:
        raise ValueError("reference_index outside electrode array")
    reference_index %= physical.shape[0]
    return np.delete(physical - physical[reference_index], reference_index, axis=0)


def reference_noise_covariance(physical_channels: int, noise_sd: float) -> np.ndarray:
    """Independent equal-variance electrode noise, referenced to one electrode.

    The shared reference contributes sigma^2 to every off-diagonal entry.
    """
    if physical_channels < 2 or not np.isfinite(noise_sd) or noise_sd <= 0:
        raise ValueError("physical_channels >= 2 and noise_sd > 0 required")
    m = physical_channels - 1
    return noise_sd**2 * (np.eye(m) + np.ones((m, m)))


def gaussian_posterior(
    observed: np.ndarray,
    leadfield: np.ndarray,
    source_covariance: np.ndarray,
    noise_covariance: np.ndarray,
) -> Posterior:
    """Gaussian linear inverse posterior; assumes zero-mean source prior.

    Posterior uncertainty is *conditional on the specified model and priors*.
    It is not a bound on biological ground-truth error.
    """
    L = _matrix(leadfield, "leadfield")
    m, n = L.shape
    y = np.asarray(observed, dtype=float)
    if y.shape != (m,) or not np.isfinite(y).all():
        raise ValueError("observed must have one finite value per sensor")
    Q = _positive_definite(source_covariance, n, "source_covariance")
    G = _positive_definite(noise_covariance, m, "noise_covariance")
    cross = Q @ L.T
    sensor_cov = L @ cross + G
    # Solves linear systems rather than explicitly inverting the sensor matrix.
    gain = np.linalg.solve(sensor_cov, cross.T).T
    mean = gain @ y
    covariance = Q - gain @ L @ Q
    covariance = (covariance + covariance.T) / 2
    return Posterior(mean, covariance, gain @ L, L @ mean)


def singular_spectrum(leadfield: np.ndarray, noise_covariance: np.ndarray) -> np.ndarray:
    """Noise-whitened singular values, largest first."""
    L = _matrix(leadfield, "leadfield")
    G = _positive_definite(noise_covariance, L.shape[0], "noise_covariance")
    whitened = np.linalg.solve(np.linalg.cholesky(G), L)
    return np.linalg.svd(whitened, compute_uv=False)


def nullspace_ambiguity(leadfield: np.ndarray) -> tuple[np.ndarray, float]:
    """Exhibit a unit source perturbation invisible to an underdetermined L."""
    L = _matrix(leadfield, "leadfield")
    m, n = L.shape
    if n <= m:
        raise ValueError("require more modeled sources than sensor measurements")
    _u, _s, vh = np.linalg.svd(L, full_matrices=True)
    z = vh[-1]
    return z, float(np.linalg.norm(L @ z))


def observability_rank(leadfield: np.ndarray, transition: np.ndarray, steps: int) -> int:
    """Rank of [L; LA; ...; LA^(steps-1)] for a *known* linear dynamic model.

    Not a claim that real neural dynamics are known or stationary.
    """
    L = _matrix(leadfield, "leadfield")
    n = L.shape[1]
    A = _matrix(transition, "transition")
    if A.shape != (n, n) or type(steps) is not int or steps < 1 or steps > 256:
        raise ValueError("transition must be NxN and steps between 1 and 256")
    blocks = []
    current = L.copy()
    for _ in range(steps):
        blocks.append(current)
        current = current @ A
        if not np.isfinite(current).all():
            raise ValueError("unstable transition generated nonfinite values")
    return int(np.linalg.matrix_rank(np.vstack(blocks)))
