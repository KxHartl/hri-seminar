"""Spike rejection between Motive and the pipeline.

Both guards exist because of one measured failure (lab 2026-08-31): partially
occluded 3-marker bodies made Motive re-solve a segment onto a different marker
assignment, the elbow angle stepped ~49 deg between two states, and the robot
reproduced that faithfully as shaking.
"""

from __future__ import annotations

import math

import numpy as np

from src.kinematics.segment_angle import elbow_flexion_angle
from src.optitrack.sdk_natnet import MAX_BODY_SPEED_MS, MedianSmoother, plausible_step


def test_median_deletes_isolated_spike():
    m = MedianSmoother(3)
    clean = [10.0, 10.1, 10.2, 10.3]
    out = [m("elbow", v) for v in clean[:2]]
    out.append(m("elbow", 60.0))          # single-frame spike
    out.append(m("elbow", clean[2]))
    assert max(out) < 11.0                # the 60 never reaches the output


def test_median_follows_a_real_move():
    m = MedianSmoother(3)
    ramp = [float(i) for i in range(20)]
    out = [m("elbow", v) for v in ramp]
    assert out[-1] >= ramp[-1] - 1.0      # at most one frame behind


def test_median_window_one_is_pass_through():
    m = MedianSmoother(1)
    assert m("elbow", 42.0) == 42.0


def test_plausible_step_accepts_human_speed():
    dt = 1 / 120
    prev = np.zeros(3)
    moved = np.array([2.0 * dt, 0.0, 0.0])          # 2 m/s — a fast arm swing
    assert plausible_step(prev, moved, dt)


def test_plausible_step_rejects_teleport():
    dt = 1 / 120
    prev = np.zeros(3)
    jumped = np.array([MAX_BODY_SPEED_MS * dt * 5, 0.0, 0.0])
    assert not plausible_step(prev, jumped, dt)


def test_plausible_step_reseeds_after_a_gap():
    prev = np.zeros(3)
    far = np.array([3.0, 0.0, 0.0])
    assert plausible_step(prev, far, dt=2.0)        # long gap: nothing to compare against


def test_elbow_angle_is_stable_near_full_extension():
    """The straight arm is the home reference, so noise must not blow up there."""
    upper, fore = np.zeros(3), np.array([0.30, 0.0, 0.0])
    hand = np.array([0.60, 0.0, 0.0])               # perfectly straight
    noise = 0.001                                    # 1 mm marker noise
    angles = []
    for dy in (-noise, 0.0, noise):
        angles.append(elbow_flexion_angle(upper, fore, hand + np.array([0.0, dy, 0.0])))
    spread = math.degrees(max(angles) - min(angles))
    assert spread < 1.0                              # ~0.4 deg for 1 mm, not tens
    assert elbow_flexion_angle(upper, fore, hand) == 0.0
