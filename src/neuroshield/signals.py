"""Deterministic illustrative EEG/EMG overlays and explicit quality gates.

Signals are synthetic, unrelated to any person's neurophysiology, and must
never be used for diagnosis or to train a medical classifier.
"""
from math import pi, sin, exp, fabs


def add_synthetic_signals(result: dict) -> dict:
    time_ms = result["traces"]["time_ms"]
    force = result["traces"]["external_force_n"]
    arm = result["scenario_detail"]["moment_arm_m"]
    eeg, emg_l, emg_r, quality = [], [], [], []
    for i, ms in enumerate(time_ms):
        t = ms / 1000
        impact_noise = 75 * exp(-((t - 0.010) / .009)**2)
        motion_noise = 12 * exp(-((t - 0.030) / .025)**2)
        artifact = (impact_noise + motion_noise) * sin(2*pi*83*t + .5)
        sample = 12*sin(2*pi*9*t) + 4*sin(2*pi*18*t + .7) + 2*sin(2*pi*3*t + .2) + artifact
        activity = exp(-((t - 0.015) / .035)**2)
        left = (12 + 48 * activity) * (0.60 * sin(2*pi*94*t) + 0.35 * sin(2*pi*121*t+.4))
        right = (12 + 42 * activity * (1 + .6 * abs(arm)/.12)) * (
            0.65 * sin(2*pi*88*t + .9) + .32 * sin(2*pi*134*t))
        q = 0.05 if abs(artifact) > 30 or force[i] > 80 else 0.35 if abs(artifact) > 12 else 0.97
        eeg.append(round(sample, 3))
        emg_l.append(round(left, 3))
        emg_r.append(round(right, 3))
        quality.append(round(q, 2))
    result["signals"] = {
        "eeg_uV": eeg, "emg_left_a_uV": emg_l, "emg_right_a_uV": emg_r, "eeg_signal_quality": quality,
        "metadata": {"source": "SYNTHETIC", "eeg_site": "illustrative scalp channel",
                     "emg_sites": ["illustrative left cervical", "illustrative right cervical"],
                     "bandpass_applied": False, "clinical_interpretation": "PROHIBITED"},
    }
    return result
