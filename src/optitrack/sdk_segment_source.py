"""Live single-DOF elbow-angle source via the official NatNet SDK (rigid bodies).

Reads the three arm-segment rigid bodies by stream ID, computes the elbow flexion
angle from the three origin positions (:func:`elbow_flexion_angle`) and re-emits it
as the canonical wrist/middle/pinky marker triple, so the unchanged single-joint
pipeline drives one robot joint. SDK connection plumbing is shared via
:class:`SDKRigidBodyReader`.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator

from src.kinematics.segment_angle import elbow_flexion_angle, encode_angle_as_markers

from .base import MarkerFrame
from .sdk_natnet import DEFAULT_IDS, DEFAULT_SDK, MedianSmoother, SDKRigidBodyReader

log = logging.getLogger(__name__)

__all__ = ["SDKSegmentSource", "DEFAULT_IDS", "DEFAULT_SDK"]


class SDKSegmentSource(SDKRigidBodyReader):
    def __init__(
        self,
        server_ip: str,
        client_ip: str = "127.0.0.1",
        ids: dict[str, int] | None = None,
        use_multicast: bool = False,
        sdk_path: str | None = None,
        scale_mm: float = 100.0,
        median: int = 3,
    ) -> None:
        super().__init__(server_ip, client_ip, use_multicast, sdk_path)
        self.ids = dict(ids or DEFAULT_IDS)
        self.scale_mm = scale_mm
        self.smooth = MedianSmoother(median)

    def __iter__(self) -> Iterator[MarkerFrame]:
        u_id, f_id, h_id = self.ids["upper"], self.ids["fore"], self.ids["hand"]
        log.info("SDK segment-source (kut lakta): ids=%s", self.ids)
        seq = 0
        missing_warned = False
        for poses in self._frames():
            if not all(i in poses for i in (u_id, f_id, h_id)):
                if not missing_warned:
                    log.warning("Nedostaju rigid bodies %s; vidljivi: %s -> preskačem.",
                                [i for i in (u_id, f_id, h_id) if i not in poses],
                                sorted(poses))
                    missing_warned = True
                continue
            missing_warned = False
            theta = self.smooth("elbow", elbow_flexion_angle(
                poses[u_id][0], poses[f_id][0], poses[h_id][0]))
            markers = encode_angle_as_markers(theta, self.scale_mm)
            yield MarkerFrame(seq=seq, t_capture=time.time(), markers=markers)
            seq += 1
