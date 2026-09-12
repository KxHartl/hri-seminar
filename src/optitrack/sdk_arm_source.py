"""Live full-arm 6-DOF source via the official NatNet SDK (rigid bodies).

Reads the three arm-segment rigid bodies (upper arm / forearm / hand) by stream ID,
including their orientation quaternions, maps them onto six joint-mimicry channels
with :class:`~src.kinematics.arm_pose.ArmPoseMapper` and emits each channel as a
named scalar 'marker' (``x`` = angle [rad]) over the existing self-describing UDP
protocol. The multi_joint pipeline maps the six channels onto the six robot joints.
SDK connection plumbing is shared via :class:`SDKRigidBodyReader`.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator

import numpy as np

from src.kinematics.arm_pose import ArmPoseMapper, RigidPose

from .base import MarkerFrame
from .sdk_natnet import DEFAULT_IDS, MedianSmoother, SDKRigidBodyReader

log = logging.getLogger(__name__)

__all__ = ["SDKArmSource"]


class SDKArmSource(SDKRigidBodyReader):
    def __init__(
        self,
        server_ip: str,
        client_ip: str = "127.0.0.1",
        ids: dict[str, int] | None = None,
        use_multicast: bool = False,
        sdk_path: str | None = None,
        axes: dict | None = None,
        median: int = 3,
    ) -> None:
        super().__init__(server_ip, client_ip, use_multicast, sdk_path)
        self.ids = dict(ids or DEFAULT_IDS)
        self.mapper = ArmPoseMapper(axes)
        self.smooth = MedianSmoother(median)

    def __iter__(self) -> Iterator[MarkerFrame]:
        u_id, f_id, h_id = self.ids["upper"], self.ids["fore"], self.ids["hand"]
        log.info("SDK arm-source (6-DOF mimikrija): ids=%s", self.ids)
        seq = 0
        missing_warned = False
        for poses in self._frames():
            if not any(i in poses for i in (u_id, f_id, h_id)):
                continue

            if not all(i in poses for i in (u_id, f_id, h_id)):
                if not missing_warned:
                    log.warning("Privremeno nedostaje dio krutih tijela %s (vidljivi: %s) — "
                                "dostupni zglobovi nastavljaju pratiti, ostali drže poziciju.",
                                [i for i in (u_id, f_id, h_id) if i not in poses],
                                sorted(poses))
                    missing_warned = True
            else:
                missing_warned = False

            up = RigidPose(*poses[u_id]) if u_id in poses else None
            fo = RigidPose(*poses[f_id]) if f_id in poses else None
            ha = RigidPose(*poses[h_id]) if h_id in poses else None

            channels = self.mapper.compute(up, fo, ha)
            if not channels:
                continue

            markers = {name: np.array([self.smooth(name, val), 0.0, 0.0], dtype=float)
                       for name, val in channels.items()}
            yield MarkerFrame(seq=seq, t_capture=time.time(), markers=markers)
            seq += 1
