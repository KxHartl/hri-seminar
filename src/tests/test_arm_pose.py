"""ArmPoseMapper: home-referencing + per-channel decomposition (synthetic quats)."""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from src.kinematics.arm_pose import CHANNELS, ArmPoseMapper, RigidPose

# Straight-arm home positions (used by the position-based elbow channel).
_UP = np.array([0.0, 0.0, 0.0])
_FO = np.array([1.0, 0.0, 0.0])
_HA = np.array([2.0, 0.0, 0.0])
_IDENT = np.array([0.0, 0.0, 0.0, 1.0])  # xyzw identity


def _pose(pos, rot: Rotation | None = None) -> RigidPose:
    quat = _IDENT if rot is None else rot.as_quat()
    return RigidPose(pos=np.asarray(pos, dtype=float), quat=quat)


def _home_poses():
    return _pose(_UP), _pose(_FO), _pose(_HA)


def test_first_call_homes_to_zero():
    m = ArmPoseMapper()
    assert not m.homed
    out = m.compute(*_home_poses())
    assert m.homed
    assert all(out[c] == pytest.approx(0.0) for c in CHANNELS)


def test_shoulder_yaw_from_upper_arm_z_rotation():
    m = ArmPoseMapper()
    m.compute(*_home_poses())                     # home = identity
    theta = math.radians(20)
    upper = _pose(_UP, Rotation.from_euler("Z", theta))
    out = m.compute(upper, _pose(_FO), _pose(_HA))
    assert out["shoulder_yaw"] == pytest.approx(theta, abs=1e-9)
    assert out["shoulder_pitch"] == pytest.approx(0.0, abs=1e-9)


def test_shoulder_pitch_from_upper_arm_x_rotation():
    m = ArmPoseMapper()
    m.compute(*_home_poses())
    phi = math.radians(-15)
    upper = _pose(_UP, Rotation.from_euler("X", phi))
    out = m.compute(upper, _pose(_FO), _pose(_HA))
    assert out["shoulder_pitch"] == pytest.approx(phi, abs=1e-9)
    assert out["shoulder_yaw"] == pytest.approx(0.0, abs=1e-9)


def test_wrist_flex_from_hand_x_rotation():
    m = ArmPoseMapper()
    m.compute(*_home_poses())
    alpha = math.radians(25)
    hand = _pose(_HA, Rotation.from_euler("X", alpha))
    out = m.compute(_pose(_UP), _pose(_FO), hand)
    assert out["wrist_flex"] == pytest.approx(alpha, abs=1e-9)
    assert out["wrist_dev"] == pytest.approx(0.0, abs=1e-9)
    assert out["wrist_axial"] == pytest.approx(0.0, abs=1e-9)


def test_wrist_axial_from_hand_z_rotation():
    m = ArmPoseMapper()
    m.compute(*_home_poses())
    gamma = math.radians(40)
    hand = _pose(_HA, Rotation.from_euler("Z", gamma))
    out = m.compute(_pose(_UP), _pose(_FO), hand)
    assert out["wrist_axial"] == pytest.approx(gamma, abs=1e-9)


def test_elbow_position_channel_tracks_bend():
    m = ArmPoseMapper()
    m.compute(*_home_poses())                     # straight -> elbow home 0
    bent_hand = _pose([1.0, 1.0, 0.0])            # fore->hand turns 90 deg
    out = m.compute(_pose(_UP), _pose(_FO), bent_hand)
    assert out["elbow"] == pytest.approx(math.pi / 2, abs=1e-9)


def test_sign_override_flips_channel():
    m = ArmPoseMapper(axes={"shoulder": {"yaw_sign": -1}})
    m.compute(*_home_poses())
    theta = math.radians(30)
    upper = _pose(_UP, Rotation.from_euler("Z", theta))
    out = m.compute(upper, _pose(_FO), _pose(_HA))
    assert out["shoulder_yaw"] == pytest.approx(-theta, abs=1e-9)


def test_wrist_axial_from_forearm_roll():
    """With axial_from_forearm, forearm roll (vs upper arm) drives wrist_axial."""
    axes = {"wrist": {"axial_from_forearm": True, "forearm_seq": "XYZ",
                      "forearm_axial_idx": 2, "forearm_axial_sign": 1}}
    m = ArmPoseMapper(axes=axes)
    m.compute(*_home_poses())
    gamma = math.radians(35)
    roll = Rotation.from_euler("Z", gamma)
    # Forearm and hand roll together -> hand-vs-forearm unchanged; forearm-vs-upper rolls.
    out = m.compute(_pose(_UP), _pose(_FO, roll), _pose(_HA, roll))
    assert out["wrist_axial"] == pytest.approx(gamma, abs=1e-9)


def test_reset_home_rehomes():
    m = ArmPoseMapper()
    m.compute(*_home_poses())
    m.reset_home()
    assert not m.homed
    out = m.compute(_pose(_UP, Rotation.from_euler("Z", 0.3)), _pose(_FO), _pose(_HA))
    assert all(out[c] == pytest.approx(0.0) for c in CHANNELS)  # new home -> zeros
