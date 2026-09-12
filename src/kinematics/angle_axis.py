"""Rotation-matrix <-> angle-axis conversion with singularity handling.

Ported from the course exercise (``02_lokalni_koordinatni_sustav.py``) with the
near-pi threshold relaxed (1e-4) for numerical robustness on streaming data.
"""

from __future__ import annotations

import numpy as np

_EPS = 1e-6
_PI_EPS = 1e-4


def rotation_matrix_to_angle_axis(R: np.ndarray) -> np.ndarray:
    """Convert a 3x3 rotation matrix to an angle-axis vector ``theta * axis`` [rad].

    Handles the two singular cases: theta ~ 0 (returns zero vector) and
    theta ~ pi (axis recovered from the matrix diagonal).
    """
    trace = float(np.clip(np.trace(R), -1.0, 3.0))
    theta = np.arccos((trace - 1.0) / 2.0)

    if abs(theta) < _EPS:
        return np.zeros(3)

    if abs(theta - np.pi) < _PI_EPS:
        diag = np.diag(R)
        k = int(np.argmax(diag))
        axis = np.zeros(3)
        axis[k] = np.sqrt(max((diag[k] + 1.0) / 2.0, 0.0))
        for i in range(3):
            if i != k and axis[k] > _EPS:
                axis[i] = R[k, i] / (2.0 * axis[k])
        n = np.linalg.norm(axis)
        if n > _EPS:
            axis = axis / n
        return theta * axis

    sin_theta = np.sin(theta)
    axis = np.array([
        R[2, 1] - R[1, 2],
        R[0, 2] - R[2, 0],
        R[1, 0] - R[0, 1],
    ]) / (2.0 * sin_theta)
    n = np.linalg.norm(axis)
    if n > _EPS:
        axis = axis / n
    return theta * axis
