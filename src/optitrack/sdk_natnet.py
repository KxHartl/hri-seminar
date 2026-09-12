"""Shared NatNet-SDK plumbing: stream rigid-body poses (by ID) to subclasses.

The hand-rolled ``src/optitrack/natnet`` parser stops at MarkerSets and cannot read
NatNet 4.0 rigid-body sections, so the live segment/arm sources use OptiTrack's
official SDK client. This base owns the parts both share — connection handshake,
the background ``new_frame_with_data_listener``, and a small bounded queue
(drop-newest under back-pressure; the pipeline's signal-timeout fail-safe covers
any gap). Subclasses implement :meth:`__iter__` to turn ``{id: (pos, quat)}`` frames
into :class:`MarkerFrame` objects.
"""

from __future__ import annotations

import logging
import os
import queue
import sys
import time
from collections import deque
from collections.abc import Iterator

import numpy as np

from .base import MarkerFrame, MarkerSource

log = logging.getLogger(__name__)

DEFAULT_SDK = (
    r"C:\Users\KHartl\Downloads\NatNet_SDK_4.5_windows"
    r"\NatNetSDK\Samples\PythonClient"
)
# role -> Motive rigid-body stream ID (lab scene defaults, re-read 2026-08-31;
# the June scene used 18/17/16 — always confirm against Motive, override with --id-*).
DEFAULT_IDS = {"upper": 25, "fore": 24, "hand": 16}

# One rigid body: (position (3,), quaternion (qx,qy,qz,qw)).
PoseById = dict[int, tuple[np.ndarray, np.ndarray]]

# A tracked arm segment cannot outrun this. Anything faster is Motive re-solving a
# partially occluded body onto a different marker assignment — measured 2026-08-31
# as ~49 deg steps in the elbow angle, which the robot faithfully reproduced as
# shaking. Such a sample is treated as a dropout, not as motion.
MAX_BODY_SPEED_MS = 7.0
STALE_AFTER_S = 0.5        # gap longer than this: re-seed instead of rejecting


class MedianSmoother:
    """Median of the last N samples per channel.

    Sits before the One-Euro filter because the two remove different things: a
    low-pass filter smears an isolated spike over its window, a median deletes it.
    N=3 costs at most one frame (~8 ms) of lag.
    """

    def __init__(self, window: int = 3) -> None:
        self.window = max(1, int(window))
        self._buf: dict[str, deque] = {}

    def __call__(self, name: str, value: float) -> float:
        if self.window == 1:
            return float(value)
        buf = self._buf.setdefault(name, deque(maxlen=self.window))
        buf.append(float(value))
        return float(np.median(buf))


def plausible_step(prev_pos: np.ndarray, pos: np.ndarray, dt: float) -> bool:
    """Could a real segment have moved from ``prev_pos`` to ``pos`` in ``dt``?"""
    if dt >= STALE_AFTER_S:
        return True                       # gap: no basis to judge, accept and re-seed
    return float(np.linalg.norm(pos - prev_pos)) <= MAX_BODY_SPEED_MS * max(dt, 1e-3)


class SDKRigidBodyReader(MarkerSource):
    def __init__(
        self,
        server_ip: str,
        client_ip: str = "127.0.0.1",
        use_multicast: bool = False,
        sdk_path: str | None = None,
    ) -> None:
        self.server_ip = server_ip
        self.client_ip = client_ip
        self.use_multicast = use_multicast
        self.sdk_path = sdk_path or os.environ.get("NATNET_SDK", DEFAULT_SDK)
        self._q: queue.Queue[PoseById] = queue.Queue(maxsize=4)
        self._nc = None
        self._last: dict[int, tuple[np.ndarray, float]] = {}
        self._rejected = 0

    def _on_frame(self, data_dict: dict) -> None:
        mocap = data_dict.get("mocap_data")
        rbd = getattr(mocap, "rigid_body_data", None)
        if rbd is None:
            return
        poses: PoseById = {}
        now = time.perf_counter()
        for rb in rbd.rigid_body_list:
            if not getattr(rb, "tracking_valid", True):
                continue
            rid = int(rb.id_num)
            pos = np.asarray(rb.pos, dtype=float)
            prev = self._last.get(rid)
            if prev is not None and not plausible_step(prev[0], pos, now - prev[1]):
                self._rejected += 1
                if self._rejected % 100 == 1:
                    log.warning("Odbačen neplauzibilan skok tijela %d (ukupno %d) — "
                                "provjeri okluziju i geometriju markera.",
                                rid, self._rejected)
                continue                  # treat as a dropout, keep the last good pose
            self._last[rid] = (pos, now)
            poses[rid] = (pos, np.asarray(rb.rot, dtype=float))
        try:
            self._q.put_nowait(poses)
        except queue.Full:
            try:                      # drop the oldest, keep the freshest pose
                self._q.get_nowait()
                self._q.put_nowait(poses)
            except queue.Empty:
                pass

    def _make_client(self):
        if self.sdk_path not in sys.path:
            sys.path.insert(0, self.sdk_path)
        try:
            from NatNetClient import NatNetClient
        except ImportError as exc:
            raise RuntimeError(
                f"NatNet SDK nije nađen u '{self.sdk_path}'. Postavi env "
                f"NATNET_SDK na ...\\NatNetSDK\\Samples\\PythonClient") from exc
        nc = NatNetClient()
        nc.set_client_address(self.client_ip)
        nc.set_server_address(self.server_ip)
        nc.set_use_multicast(self.use_multicast)
        nc.new_frame_with_data_listener = self._on_frame
        if hasattr(nc, "set_print_level"):
            nc.set_print_level(0)     # SDK prints every Nth frame by default — silence it
        return nc

    def _frames(self) -> Iterator[PoseById]:
        """Yield ``{id: (pos, quat)}`` dicts from the live SDK stream."""
        nc = self._make_client()
        if not nc.run():
            raise RuntimeError("NatNet SDK run() nije uspio (provjeri vezu/IP-ove).")
        self._nc = nc
        log.info("SDK rigid-body reader: server=%s client=%s multicast=%s",
                 self.server_ip, self.client_ip, self.use_multicast)
        while True:
            try:
                yield self._q.get(timeout=2.0)
            except queue.Empty:
                log.warning("Nema rigid-body okvira 2 s (streaming/ID-ovi?).")
                continue

    def __iter__(self) -> Iterator[MarkerFrame]:  # pragma: no cover - abstract
        raise NotImplementedError

    def close(self) -> None:
        if self._nc is not None:
            try:
                self._nc.shutdown()
            except Exception:  # noqa: BLE001 - best-effort teardown
                pass
            self._nc = None
