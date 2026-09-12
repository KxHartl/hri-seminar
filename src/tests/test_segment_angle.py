"""Segment-angle kinematics: elbow flexion + canonical-triple round-trip."""

from __future__ import annotations

import math

import numpy as np
import pytest

from src.kinematics.hand_frame import hand_frame_single
from src.kinematics.joint_angle import flexion_angle
from src.kinematics.segment_angle import elbow_flexion_angle, encode_angle_as_markers


def test_straight_arm_is_zero():
    upper = np.array([0.0, 0.0, 0.0])
    fore = np.array([1.0, 0.0, 0.0])
    hand = np.array([2.0, 0.0, 0.0])
    assert elbow_flexion_angle(upper, fore, hand) == pytest.approx(0.0, abs=1e-9)


def test_right_angle_elbow():
    upper = np.array([0.0, 0.0, 0.0])
    fore = np.array([1.0, 0.0, 0.0])      # upper->fore along +x
    hand = np.array([1.0, 1.0, 0.0])      # fore->hand along +y  => 90 deg bend
    assert elbow_flexion_angle(upper, fore, hand) == pytest.approx(math.pi / 2, abs=1e-9)


def test_scale_invariant():
    upper = np.array([0.0, 0.0, 0.0])
    fore = np.array([3.0, 0.0, 0.0])
    hand = np.array([3.0, 3.0, 0.0])
    # Same shape scaled up by 1000 (m vs mm) -> identical angle.
    assert elbow_flexion_angle(upper, fore, hand) == pytest.approx(
        elbow_flexion_angle(upper * 1000, fore * 1000, hand * 1000), abs=1e-12)


def test_degenerate_returns_zero():
    p = np.array([1.0, 2.0, 3.0])
    assert elbow_flexion_angle(p, p, p) == 0.0


@pytest.mark.parametrize("theta", [-1.0, -0.3, 0.0, 0.2, 0.7, 1.2])
def test_encode_roundtrip_recovers_angle(theta):
    """The pipeline's hand_frame -> flexion_angle must recover the encoded angle.

    Reference is the straight (theta=0) frame, mirroring the pipeline using the
    first frame as the zero-flexion reference.
    """
    m_ref = encode_angle_as_markers(0.0)
    R_ref, _ = hand_frame_single(m_ref["zapesce"], m_ref["srednji"], m_ref["mali"])

    m = encode_angle_as_markers(theta)
    R, ok = hand_frame_single(m["zapesce"], m["srednji"], m["mali"])
    assert ok
    assert flexion_angle(R, R_ref) == pytest.approx(theta, abs=1e-9)
