"""Deterministic S0 spatial mixing experiment with falsifiable controls."""
from __future__ import annotations

import hashlib
import json

import numpy as np

from .inverse import (
    gaussian_posterior,
    independent_reference,
    nullspace_ambiguity,
    reference_noise_covariance,
    singular_spectrum,
)


def make_toy_experiment(seed: int = 2026, channels: int = 24, sources: int = 96) -> dict:
    """Construct a smooth, non-anatomical leadfield and sparse source signal.

    No BEM/FEM, scalp anatomy, neural ground truth, or behavior is modeled.
    """
    if type(seed) is not int or type(channels) is not int or type(sources) is not int:
        raise ValueError("seed, channels and sources must be integers")
    if not 4 <= channels <= 128 or not channels < sources <= 1024:
        raise ValueError("require 4 <= channels < sources <= 1024")
    rng = np.random.default_rng(seed)
    electrodes = np.linspace(0.02, 0.98, channels)
    positions = np.linspace(0, 1, sources)
    spread = 0.085
    forward = np.exp(-0.5 * ((electrodes[:, None] - positions[None, :]) / spread) ** 2)
    # Avoid a hidden amplitude scale change across configurations.
    forward /= np.linalg.norm(forward, axis=1, keepdims=True)
    L = independent_reference(forward)
    source = (1.7 * np.exp(-0.5 * ((positions - .27) / .025) ** 2)
              - 1.2 * np.exp(-0.5 * ((positions - .68) / .035) ** 2))
    sigma = .012
    independent_electrode_noise = rng.normal(0, sigma, channels)
    measured = L @ source + independent_electrode_noise[:-1] - independent_electrode_noise[-1]
    distances = positions[:, None] - positions[None, :]
    Q = 0.5 * np.exp(-0.5 * (distances / .065) ** 2) + .025 * np.eye(sources)
    G = reference_noise_covariance(channels, sigma)
    return {"leadfield": L, "source": source, "measured": measured, "Q": Q, "G": G}


def run_toy_experiment(seed: int = 2026, channels: int = 24, sources: int = 96) -> dict:
    experiment = make_toy_experiment(seed, channels, sources)
    L, x, y = (experiment[k] for k in ("leadfield", "source", "measured"))
    posterior = gaussian_posterior(y, L, experiment["Q"], experiment["G"])
    spectrum = singular_spectrum(L, experiment["G"])
    _invisible_source, residual = nullspace_ambiguity(L)
    payload = {
        "schema_version": "neurospatial-toy-0.1.0",
        "origin": "SYNTHETIC",
        "evidence_level": "S0",
        "leadfield_type": "1d_gaussian_spatial_kernel_NOT_a_head_model",
        "model_assumption": "zero_mean_gaussian_source_prior_with_known_leadfield_and_noise_covariance",
        "seed": seed,
        "physical_electrodes": channels,
        "independent_referenced_measurements": L.shape[0],
        "modeled_sources": sources,
        "leadfield_rank": int(np.linalg.matrix_rank(L)),
        "nullspace_residual_l2": residual,
        "source_relative_l2_error": float(np.linalg.norm(posterior.mean - x) / np.linalg.norm(x)),
        "measured_relative_l2_residual": float(np.linalg.norm(posterior.predicted_sensors - y) / np.linalg.norm(y)),
        "resolution_trace": float(np.trace(posterior.resolution)),
        "posterior_sd_median_model_conditional": float(np.median(np.sqrt(np.clip(np.diag(posterior.covariance), 0, None)))),
        "noise_whitened_singular_values": [float(v) for v in spectrum],
        "claim_boundary": "This is a spatial mixing toy example, not source localization on a human head, a behavioral intervention, or thought decoding.",
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    payload["report_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    return payload
