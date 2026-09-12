"""Numerical correctness of hand-frame and angle-axis math."""

from __future__ import annotations

import numpy as np
from scipy.spatial.transform import Rotation

from src.optitrack.csv_loader import load_take
from src.kinematics.angle_axis import rotation_matrix_to_angle_axis
from src.kinematics.hand_frame import hand_frames
from src.kinematics.joint_angle import flexion_series
from .conftest import VJEZBE_02


def test_angle_axis_round_trip_random():
    rng = np.random.default_rng(42)
    for _ in range(200):
        rotvec = rng.normal(0, 1, 3)
        rotvec = rotvec / np.linalg.norm(rotvec) * rng.uniform(0, np.pi)
        R = Rotation.from_rotvec(rotvec).as_matrix()
        aa = rotation_matrix_to_angle_axis(R)
        R_back = Rotation.from_rotvec(aa).as_matrix()
        assert np.linalg.norm(R - R_back) < 1e-6


def test_angle_axis_singularities():
    # theta ~ 0
    assert np.linalg.norm(rotation_matrix_to_angle_axis(np.eye(3))) < 1e-9
    # theta ~ pi about X
    R = Rotation.from_rotvec([np.pi, 0, 0]).as_matrix()
    aa = rotation_matrix_to_angle_axis(R)
    R_back = Rotation.from_rotvec(aa).as_matrix()
    assert np.linalg.norm(R - R_back) < 1e-4


def test_hand_frames_orthonormal_on_real_data():
    take = load_take(VJEZBE_02 / "hri_snimanje_vjezbe_02_y.csv")
    R, ok = hand_frames(
        take.markers["zapesce"], take.markers["srednji"], take.markers["mali"]
    )
    assert ok.mean() > 0.99  # essentially all frames valid
    # Sample a spread of frames for the orthonormality check.
    for i in np.linspace(0, R.shape[0] - 1, 50, dtype=int):
        err = np.max(np.abs(R[i].T @ R[i] - np.eye(3)))
        assert err < 1e-9
        assert abs(np.linalg.det(R[i]) - 1.0) < 1e-9


def test_flexion_zero_at_reference_and_continuous():
    take = load_take(VJEZBE_02 / "hri_snimanje_vjezbe_02_x.csv")
    angle, ok = flexion_series(
        take.markers["zapesce"], take.markers["srednji"], take.markers["mali"],
        reference_idx=0,
    )
    assert abs(angle[0]) < 1e-9
    # No spurious jumps: per-frame change stays small at 120 Hz.
    assert np.max(np.abs(np.diff(angle))) < np.radians(20)
