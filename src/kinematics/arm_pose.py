"""Full-arm 6-DOF pose mapping from three rigid-body poses (joint mimicry).

Maps the three arm-segment rigid bodies (upper arm / forearm / hand, each with a
position AND orientation quaternion) onto six robot joints, by joint mimicry — NOT
inverse kinematics. Every channel is measured **relative to a home pose** (the
straight-arm pose captured at the first frame), so all six channels are ``0`` at
home and the robot starts from its own home ``q``.

Channels (semantic; the pipeline maps each onto a robot joint via ``arm_mapping``):

    shoulder_yaw    upper-arm azimuth (left/right) vs world home   -> base    (J0)
    shoulder_pitch  upper-arm elevation (up/down)  vs world home   -> shoulder (J1)
    elbow           forearm vs upper arm (up/down)                 -> elbow    (J2)
    wrist_flex      hand vs forearm (up/down)                      -> wrist_1  (J3)
    wrist_dev       hand vs forearm (left/right)                   -> wrist_2  (J4)
    wrist_axial     hand vs forearm (about the long axis)          -> wrist_3  (J5)

Orientation maths uses :class:`scipy.spatial.transform.Rotation`. NatNet streams
quaternions as ``(qx, qy, qz, qw)`` (scalar-last), which is exactly scipy's
``from_quat`` convention. WHICH Euler sequence / index / sign corresponds to each
channel depends on how the rigid-body local axes were defined in Motive, so it is
**not hard-coded** — it comes from the ``arm_axes`` config, filled in by the
calibration pass (``testing/lab/diag/arm_inspect.py``).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial.transform import Rotation

from .segment_angle import elbow_flexion_angle

CHANNELS = (
    "shoulder_yaw", "shoulder_pitch", "elbow",
    "wrist_flex", "wrist_dev", "wrist_axial",
)

# Reasonable starting guesses; the calibration pass overrides these in config.
DEFAULT_AXES = {
    "shoulder": {"seq": "ZXY", "yaw_idx": 0, "yaw_sign": 1,
                 "pitch_idx": 1, "pitch_sign": 1},
    "elbow": {"mode": "position", "sign": 1},   # position | orientation
    "wrist": {"seq": "XYZ", "flex_idx": 0, "dev_idx": 1, "axial_idx": 2,
              "signs": [1, 1, 1]},
}


@dataclass(frozen=True)
class RigidPose:
    """One rigid body: origin position (3,) and orientation quaternion (qx,qy,qz,qw)."""

    pos: np.ndarray
    quat: np.ndarray

    def rot(self) -> Rotation:
        return Rotation.from_quat(np.asarray(self.quat, dtype=float))


class ArmPoseMapper:
    """Stateful mapper: 3 rigid poses -> 6 channel angles [rad], homed at first call.

    The first ``compute`` captures the home reference and returns all-zero channels;
    every later call returns the deviation of each channel from home.
    """

    def __init__(self, axes: dict | None = None) -> None:
        self.cfg = _merge_axes(axes)
        self._home: dict | None = None

    def reset_home(self) -> None:
        """Forget the reference so the next ``compute`` re-homes."""
        self._home = None

    @property
    def homed(self) -> bool:
        return self._home is not None

    def compute(
        self,
        upper: RigidPose | None = None,
        fore: RigidPose | None = None,
        hand: RigidPose | None = None,
    ) -> dict[str, float]:
        if self._home is None:
            if upper is None or fore is None or hand is None:
                return {}
            R_U, R_F, R_H = upper.rot(), fore.rot(), hand.rot()
            self._home = {
                "U": R_U, "F": R_F, "H": R_H,
                "elbow_pos": elbow_flexion_angle(upper.pos, fore.pos, hand.pos),
            }
            return {c: 0.0 for c in CHANNELS}

        res: dict[str, float] = {}

        if upper is not None:
            R_U = upper.rot()
            sh = self.cfg["shoulder"]
            e_sh = (self._home["U"].inv() * R_U).as_euler(sh["seq"])
            res["shoulder_yaw"] = sh["yaw_sign"] * float(e_sh[sh["yaw_idx"]])
            res["shoulder_pitch"] = sh["pitch_sign"] * float(e_sh[sh["pitch_idx"]])

        if upper is not None and fore is not None:
            R_U, R_F = upper.rot(), fore.rot()
            el = self.cfg["elbow"]
            if el.get("mode", "position") == "position":
                if hand is not None:
                    res["elbow"] = el.get("sign", 1) * (
                        elbow_flexion_angle(upper.pos, fore.pos, hand.pos)
                        - self._home["elbow_pos"])
            else:
                R_el_home = self._home["U"].inv() * self._home["F"]
                R_el_cur = R_U.inv() * R_F
                e_el = (R_el_home.inv() * R_el_cur).as_euler(el.get("seq", "XYZ"))
                res["elbow"] = el.get("sign", 1) * float(e_el[el.get("idx", 0)])

            wr = self.cfg["wrist"]
            if wr.get("axial_from_forearm"):
                R_fa_home = self._home["U"].inv() * self._home["F"]
                R_fa_cur = R_U.inv() * R_F
                e_fa = (R_fa_home.inv() * R_fa_cur).as_euler(wr.get("forearm_seq", "XYZ"))
                res["wrist_axial"] = wr.get("forearm_axial_sign", 1) * float(e_fa[wr.get("forearm_axial_idx", 2)])

        if fore is not None and hand is not None:
            R_F, R_H = fore.rot(), hand.rot()
            wr = self.cfg["wrist"]
            R_wr_home = self._home["F"].inv() * self._home["H"]
            R_wr_cur = R_F.inv() * R_H
            e_wr = (R_wr_home.inv() * R_wr_cur).as_euler(wr["seq"])
            s = wr["signs"]
            res["wrist_flex"] = s[0] * float(e_wr[wr["flex_idx"]])
            res["wrist_dev"] = s[1] * float(e_wr[wr["dev_idx"]])
            if not wr.get("axial_from_forearm"):
                res["wrist_axial"] = s[2] * float(e_wr[wr["axial_idx"]])

        return res


def _merge_axes(axes: dict | None) -> dict:
    """Overlay a (partial) axes config on top of DEFAULT_AXES."""
    merged = {k: dict(v) for k, v in DEFAULT_AXES.items()}
    for body, sub in (axes or {}).items():
        merged.setdefault(body, {}).update(sub)
    return merged
