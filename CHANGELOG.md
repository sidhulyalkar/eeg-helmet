## V0.3.0: numerical cross-check (2026-10-23)
- Independently expressed RK4 solution of the same synthetic equations, including applied work, mechanical energy storage, progressive stop energy, and damping.
- Cross-solver report: 4 impact scenarios x 4 bounded design configurations, strict numerical-only pass/fail gates, source SHA-256s, case-level failures and conservative energy accounting.
- Analytical harmonic oscillator RK4 test, failure-injection regression tests, numerical-audit command, CI matrix integration.
- Still S0 synthetic and unvalidated; zero concussion, protection or hardware qualification claims.

# Changelog

## V0.2.0 (2026-10-23)

- Added bounded variable-step simulation for discretization sensitivity challenges.
- Added four-resolution numerical qualification CLI and localhost dashboard report. Passing does NOT change S0 evidence status.
- Added explicit synthetic-only multimodal channel and session validator with unit, timing-gap, amplitude finiteness and quality checks.
- Added local fixture generator and regression tests.
- Preserved V0.1 visualization, design-space sweep, reproducibility fingerprints, and fail-closed demo policy.

## V0.1.0

- First deterministic reduced-order impact workbench with synthetic EEG/EMG visualization.
