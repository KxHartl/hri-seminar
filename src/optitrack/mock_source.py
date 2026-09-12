"""Synthetic marker sources — a virtual arm, no hardware needed.

Implement the same :class:`MarkerSource` interface as ``ReplaySource`` and the
live sources, so the whole path (bridge -> UDP -> pipeline -> robot) can be
smoke-tested without Motive.

  * :class:`MockMarkerSource` -- four hand markers whose flexion angle varies
    sinusoidally about the hand's lateral axis (single-joint path).
  * :class:`MockArmSource` -- the six arm channels as named scalars, exactly the
    shape :class:`~src.optitrack.sdk_arm_source.SDKArmSource` emits, so the
    6-DOF ``--mode multi_joint`` path can be rehearsed dry before the lab.
"""

from __future__ import annotations

import time
from collections.abc import Iterator

import numpy as np

from .base import MarkerFrame, MarkerSource

# Base hand geometry [mm], in a frame where X = wrist->middle, Z = palm normal.
_BASE = {
    "zapesce": np.array([0.0, 0.0, 0.0]),
    "srednji": np.array([100.0, 0.0, 0.0]),
    "mali": np.array([10.0, 55.0, 0.0]),
    "palac": np.array([30.0, -40.0, 0.0]),
}


def _rot_y(theta: float) -> np.ndarray:
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


class MockMarkerSource(MarkerSource):
    """Virtual hand with sinusoidal flexion (about the lateral Y axis)."""

    def __init__(
        self,
        rate_hz: float = 120.0,
        amplitude_deg: float = 30.0,
        freq_hz: float = 0.3,
        noise_mm: float = 0.3,
        realtime: bool = True,
        seed: int = 0,
    ) -> None:
        self.rate_hz = float(rate_hz)
        self.amp = np.radians(amplitude_deg)
        self.freq = float(freq_hz)
        self.noise_mm = float(noise_mm)
        self.realtime = realtime
        self._rng = np.random.default_rng(seed)

    def __iter__(self) -> Iterator[MarkerFrame]:
        dt = 1.0 / self.rate_hz
        seq = 0
        t0 = time.perf_counter()
        while True:
            if self.realtime:
                deadline = t0 + seq * dt
                sleep = deadline - time.perf_counter()
                if sleep > 0:
                    time.sleep(sleep)
            theta = self.amp * np.sin(2.0 * np.pi * self.freq * seq * dt)
            R = _rot_y(theta)
            wrist = _BASE["zapesce"]
            markers = {}
            for name, p in _BASE.items():
                pos = wrist + R @ (p - wrist)
                if self.noise_mm:
                    pos = pos + self._rng.normal(0.0, self.noise_mm, 3)
                markers[name] = pos
            yield MarkerFrame(seq=seq, t_capture=time.time(), markers=markers)
            seq += 1


class MockArmSource(MarkerSource):
    """Virtual 6-DOF arm: each channel a named scalar, as the SDK arm source sends.

    Channels move at different rates and amplitudes so a dry run shows every joint
    doing something distinguishable, and each joint's own limits get exercised.
    """

    # channel -> (amplitude [deg], frequency [Hz])
    CHANNELS = {
        "shoulder_yaw": (20.0, 0.13),
        "shoulder_pitch": (15.0, 0.17),
        "elbow": (40.0, 0.23),
        "wrist_flex": (25.0, 0.31),
        "wrist_dev": (15.0, 0.19),
        "wrist_axial": (30.0, 0.11),
    }

    def __init__(
        self,
        rate_hz: float = 120.0,
        noise_deg: float = 0.4,
        realtime: bool = True,
        seed: int = 0,
    ) -> None:
        self.rate_hz = float(rate_hz)
        self.noise = np.radians(noise_deg)
        self.realtime = realtime
        self._rng = np.random.default_rng(seed)

    def __iter__(self) -> Iterator[MarkerFrame]:
        dt = 1.0 / self.rate_hz
        seq = 0
        t0 = time.perf_counter()
        while True:
            if self.realtime:
                deadline = t0 + seq * dt
                sleep = deadline - time.perf_counter()
                if sleep > 0:
                    time.sleep(sleep)
            t = seq * dt
            markers = {}
            for name, (amp_deg, freq) in self.CHANNELS.items():
                if name in ("elbow", "shoulder_pitch"):
                    # Physiological motion: flexion and elevation are non-negative relative to home
                    val = np.radians(amp_deg) * 0.5 * (1.0 - np.cos(2.0 * np.pi * freq * t))
                else:
                    val = np.radians(amp_deg) * np.sin(2.0 * np.pi * freq * t)
                if self.noise:
                    val += self._rng.normal(0.0, self.noise)
                # Same encoding the SDK arm source uses: scalar in x.
                markers[name] = np.array([val, 0.0, 0.0])
            yield MarkerFrame(seq=seq, t_capture=time.time(), markers=markers)
            seq += 1
