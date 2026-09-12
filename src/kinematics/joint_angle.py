"""Single-DOF hand-flexion angle, relative to a reference frame.

Flexion is the up/down bending of the hand about its lateral axis. We measure it
as the rotation of the hand-pointing direction (frame X axis) in the reference
frame's X-Z plane: ``flexion = atan2(x_in_ref.z, x_in_ref.x)``, where ``x_in_ref``
is the current X axis expressed in reference-frame coordinates. This is exactly
zero at the reference pose, is a smooth scalar free of Euler-gimbal issues for the
single DOF we control, and maps directly onto one UR joint (wrist_1 / J4).
"""

from __future__ import annotations

import numpy as np

from .hand_frame import hand_frames


def flexion_angle(R: np.ndarray, R_ref: np.ndarray) -> float:
    """Flexion of a single hand frame ``R`` relative to ``R_ref`` [rad]."""
    x_cur = R[:, 0]
    x_in_ref = R_ref.T @ x_cur
    return float(np.arctan2(x_in_ref[2], x_in_ref[0]))


def flexion_series(
    wrist: np.ndarray,
    middle: np.ndarray,
    pinky: np.ndarray,
    reference_idx: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute the flexion-angle time series for a take.

    Args:
        wrist, middle, pinky: (n_frames, 3) marker trajectories.
        reference_idx: frame used as the zero-flexion reference.

    Returns:
        (angle_rad, ok) — angle shape (n_frames,), ok validity mask (n_frames,).
    """
    R, ok = hand_frames(wrist, middle, pinky)
    R_ref = R[reference_idx]
    angle = np.array([flexion_angle(R[i], R_ref) for i in range(R.shape[0])])
    return angle, ok


def sensitivity(
    wrist: np.ndarray,
    middle: np.ndarray,
    pinky: np.ndarray,
    noise_mm: float = 1.0,
    n_trials: int = 20,
    reference_idx: int = 0,
    seed: int = 0,
) -> dict[str, float]:
    """Monte-Carlo sensitivity of the flexion angle to marker measurement noise.

    Adds zero-mean Gaussian noise (std ``noise_mm``) to every marker and reports
    the RMS deviation of the resulting flexion series, in degrees.

    Returns:
        dict with ``rms_deg``, ``max_deg`` and the input ``noise_mm``.
    """
    rng = np.random.default_rng(seed)
    base, _ = flexion_series(wrist, middle, pinky, reference_idx)
    devs = []
    for _ in range(n_trials):
        w = wrist + rng.normal(0.0, noise_mm, wrist.shape)
        m = middle + rng.normal(0.0, noise_mm, middle.shape)
        p = pinky + rng.normal(0.0, noise_mm, pinky.shape)
        pert, _ = flexion_series(w, m, p, reference_idx)
        devs.append(pert - base)
    devs = np.degrees(np.asarray(devs))
    return {
        "noise_mm": noise_mm,
        "rms_deg": float(np.sqrt(np.mean(devs ** 2))),
        "max_deg": float(np.max(np.abs(devs))),
    }
