"""Replay an OptiTrack take as a real-time marker stream / UDP sender.

Lets the *same* downstream pipeline run against recorded data now and a live
OptiTrack stream later. Emits frames at the take's native rate using
``perf_counter`` deadline scheduling (no cumulative drift) and can inject
artificial packet loss to exercise the receiver's robustness.
"""

from __future__ import annotations

import logging
import socket
import time
from collections.abc import Iterator
from pathlib import Path

import numpy as np

from . import protocol
from .base import MarkerFrame, MarkerSource
from .csv_loader import OptiTrackTake, load_take

log = logging.getLogger(__name__)


class ReplaySource(MarkerSource):
    """Yields :class:`MarkerFrame` from a take at (scaled) real-time cadence."""

    def __init__(
        self,
        take: OptiTrackTake | str | Path,
        marker_names: tuple[str, ...] = ("zapesce", "palac", "srednji", "mali"),
        loop: bool = False,
        speed: float = 1.0,
        realtime: bool = True,
    ) -> None:
        if not isinstance(take, OptiTrackTake):
            take = load_take(take, marker_names=marker_names)
        self.take = take
        self.loop = loop
        self.speed = float(speed)
        self.realtime = realtime
        self._dt = (1.0 / take.frame_rate_hz) / self.speed

    def __iter__(self) -> Iterator[MarkerFrame]:
        seq = 0
        t0 = time.perf_counter()
        emitted = 0
        while True:
            for i in range(self.take.n_frames):
                if self.realtime:
                    deadline = t0 + emitted * self._dt
                    sleep = deadline - time.perf_counter()
                    if sleep > 0:
                        time.sleep(sleep)
                markers = {name: self.take.markers[name][i]
                           for name in self.take.markers}
                # Wall clock (time.time) so capture->command latency is comparable
                # across processes/machines; perf_counter (above) drives cadence.
                yield MarkerFrame(seq=seq, t_capture=time.time(),
                                  markers=markers)
                seq += 1
                emitted += 1

class TrackReplaySource(MarkerSource):
    """Yields :class:`MarkerFrame` from a recorded 6-DOF .track.csv at real-time cadence."""

    CHANNEL_COLS = {
        "shoulder_yaw": "in_J1_deg",
        "shoulder_pitch": "in_J2_deg",
        "elbow": "in_J3_deg",
        "wrist_flex": "in_J4_deg",
        "wrist_dev": "in_J5_deg",
        "wrist_axial": "in_J6_deg",
    }

    def __init__(
        self,
        track_path: str | Path,
        loop: bool = False,
        speed: float = 1.0,
        realtime: bool = True,
        rate_hz: float = 120.0,
    ) -> None:
        import csv
        self.track_path = Path(track_path)
        self.loop = loop
        self.speed = float(speed)
        self.realtime = realtime
        self.rate_hz = rate_hz
        self._dt = (1.0 / rate_hz) / self.speed
        self.frames: list[tuple[float, dict[str, np.ndarray]]] = []

        with open(self.track_path, "r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            last_valid: dict[str, float] = {}
            for idx, row in enumerate(reader):
                t_rel = float(row["t_s"]) if "t_s" in row and row["t_s"] != "" else idx * self._dt
                markers = {}
                for ch, col in self.CHANNEL_COLS.items():
                    if col in row and row[col] != "":
                        val = float(row[col])
                        filt_col = col.replace("in_", "filt_")
                        filt_val = float(row.get(filt_col, 0.0)) if filt_col in row and row[filt_col] != "" else val
                        # In the lab log, in=0 and filt=0 represents a hold tick where no new frame was received
                        if val == 0.0 and filt_val == 0.0 and ch in last_valid:
                            val = last_valid[ch]
                        else:
                            last_valid[ch] = val
                        markers[ch] = np.array([np.radians(val), 0.0, 0.0])
                if markers:
                    self.frames.append((t_rel, markers))

    def __iter__(self) -> Iterator[MarkerFrame]:
        seq = 0
        t0 = time.perf_counter()
        while True:
            for t_rel, markers in self.frames:
                if self.realtime:
                    deadline = t0 + t_rel / self.speed
                    sleep = deadline - time.perf_counter()
                    if sleep > 0:
                        time.sleep(sleep)
                yield MarkerFrame(seq=seq, t_capture=time.time(), markers=markers)
                seq += 1
            if not self.loop:
                return


def send_over_udp(
    source: MarkerSource,
    host: str,
    port: int,
    drop_rate: float = 0.0,
    seed: int = 0,
) -> None:
    """Stream a marker source out over UDP, optionally dropping packets."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    rng = np.random.default_rng(seed)
    sent = dropped = 0
    try:
        for frame in source:
            if drop_rate > 0.0 and rng.random() < drop_rate:
                dropped += 1
                continue
            sock.sendto(protocol.encode(frame), (host, port))
            sent += 1
    finally:
        sock.close()
        log.info("UDP slanje gotovo: poslano=%d odbačeno=%d", sent, dropped)
