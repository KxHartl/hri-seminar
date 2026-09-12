"""Local hand coordinate frame from marker positions (cross-product method).

Origin at the wrist; X = wrist->middle (primary axis); Z = X x (wrist->pinky)
(palm normal); Y = Z x X. This guarantees an orthonormal frame. Adapted from the
course exercise, with the degenerate-frame fallback improved to reuse the
*previous* valid frame instead of a fixed axis, avoiding discontinuities when the
hand briefly collapses (markers near-collinear).
"""

from __future__ import annotations

import numpy as np

_EPS = 1e-6


def _safe_unit(v: np.ndarray, fallback: np.ndarray) -> tuple[np.ndarray, bool]:
    n = np.linalg.norm(v)
    if n < _EPS:
        return fallback, False
    return v / n, True


def hand_frame_single(
    wrist: np.ndarray,
    middle: np.ndarray,
    pinky: np.ndarray,
    prev_R: np.ndarray | None = None,
) -> tuple[np.ndarray, bool]:
    """Build one orthonormal hand frame.

    Args:
        wrist, middle, pinky: (3,) marker positions.
        prev_R: previous frame's rotation matrix, used as fallback on degeneracy.

    Returns:
        (R, ok) where R is 3x3 with columns [X|Y|Z]; ok is False if a fallback
        axis had to be used (degenerate configuration).
    """
    fb_x = prev_R[:, 0] if prev_R is not None else np.array([1.0, 0.0, 0.0])
    fb_z = prev_R[:, 2] if prev_R is not None else np.array([0.0, 0.0, 1.0])

    x_axis, ok_x = _safe_unit(middle - wrist, fb_x)
    aux = pinky - wrist
    z_axis, ok_z = _safe_unit(np.cross(x_axis, aux), fb_z)
    # Re-orthogonalise Y, then X to guarantee a proper orthonormal basis.
    y_axis = np.cross(z_axis, x_axis)
    ny = np.linalg.norm(y_axis)
    if ny < _EPS:
        y_axis = prev_R[:, 1] if prev_R is not None else np.array([0.0, 1.0, 0.0])
    else:
        y_axis = y_axis / ny
    x_axis = np.cross(y_axis, z_axis)

    R = np.column_stack([x_axis, y_axis, z_axis])
    return R, (ok_x and ok_z and ny >= _EPS)


def hand_frames(
    wrist: np.ndarray,
    middle: np.ndarray,
    pinky: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Vectorised over frames.

    Args:
        wrist, middle, pinky: (n_frames, 3) marker trajectories.

    Returns:
        (R, ok) with R shape (n_frames, 3, 3) and ok shape (n_frames,) bool.
    """
    n = wrist.shape[0]
    R = np.zeros((n, 3, 3))
    ok = np.zeros(n, dtype=bool)
    prev: np.ndarray | None = None
    for i in range(n):
        Ri, oki = hand_frame_single(wrist[i], middle[i], pinky[i], prev)
        R[i] = Ri
        ok[i] = oki
        prev = Ri
    return R, ok
