"""Elbow flexion angle from three arm-segment rigid-body origins.

The OptiTrack scene defines three rigid bodies — upper arm (``nadlaktica``),
forearm (``podlaktica``) and hand (``saka``) — each streamed with its own origin.
The elbow flexion is the angle of the polyline upper-arm -> forearm -> hand: the
deviation from a straight arm, ``0`` at full extension and growing as the elbow
bends. Using only the three origin POSITIONS makes it independent of how each
rigid body's local axes were defined in Motive (no quaternion convention to get
wrong).

The angle is then re-encoded as the canonical wrist/middle/pinky marker triple via
:func:`encode_angle_as_markers`, so the *unchanged*, already-tested pipeline
(``hand_frame_single`` -> ``flexion_angle`` -> filter -> safety -> servoJ) drives
the robot from a precomputed scalar. The bridge owns "what angle to command"; the
pipeline owns "how to command it safely".
"""

from __future__ import annotations

import math

import numpy as np

_EPS = 1e-9


def elbow_flexion_angle(
    upper: np.ndarray, fore: np.ndarray, hand: np.ndarray
) -> float:
    """Elbow flexion [rad] from three segment origins.

    Args:
        upper, fore, hand: (3,) origin positions of the upper-arm, forearm and
            hand rigid bodies (any consistent length unit; the result is
            scale-invariant).

    Returns:
        The angle between the upper-arm direction (``upper -> fore``) and the
        forearm direction (``fore -> hand``): ``0`` rad for a straight arm,
        increasing toward ``pi`` as the elbow bends. Returns ``0.0`` for a
        degenerate (near-zero-length) configuration.
    """
    a = np.asarray(fore, dtype=float) - np.asarray(upper, dtype=float)
    b = np.asarray(hand, dtype=float) - np.asarray(fore, dtype=float)
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    if na < _EPS or nb < _EPS:
        return 0.0
    # atan2(|a x b|, a.b) rather than acos(a.b/|a||b|): acos has an infinite
    # derivative at 0 and pi, and the straight arm — our home reference, where the
    # operator spends most of the time — sits exactly on that singularity, so
    # millimetre marker noise came out as degrees of angle noise.
    cross = float(np.linalg.norm(np.cross(a, b)))
    return math.atan2(cross, float(np.dot(a, b)))


def encode_angle_as_markers(
    theta: float,
    scale_mm: float = 100.0,
    *,
    wrist_name: str = "zapesce",
    middle_name: str = "srednji",
    pinky_name: str = "mali",
) -> dict[str, np.ndarray]:
    """Encode a scalar flexion angle into the canonical marker triple.

    The three points realise a rotation by ``theta`` about the hand-frame Y axis,
    so ``hand_frame_single`` followed by ``flexion_angle`` recovers exactly
    ``theta`` (relative to whichever frame the pipeline picks as reference). This
    lets a precomputed angle drive the unchanged pipeline. Marker names default to
    those in ``src/config/default.yaml`` (``zapesce``/``srednji``/``mali``).
    """
    c, s = math.cos(theta), math.sin(theta)
    return {
        wrist_name: np.zeros(3, dtype=float),
        middle_name: np.array([c, 0.0, s], dtype=float) * scale_mm,
        pinky_name: np.array([0.0, 1.0, 0.0], dtype=float) * scale_mm,
    }
