"""Mock live path: MockMarkerSource -> send_over_udp -> receiver (no Motive).

Validates that the live bridge wiring delivers correctly-named markers and a
varying flexion signal, reusing the verified UDP transport.
"""

from __future__ import annotations

import itertools
import threading
import time

import numpy as np

from src.optitrack.mock_source import MockArmSource, MockMarkerSource
from src.optitrack.replay_source import send_over_udp
from src.kinematics.joint_angle import flexion_angle
from src.kinematics.hand_frame import hand_frame_single
from src.receiver import UDPReceiver


def test_mock_source_markers_and_flexion_varies():
    src = MockMarkerSource(rate_hz=120.0, realtime=False, noise_mm=0.0)
    frames = list(itertools.islice(iter(src), 500))  # >= one full 0.3 Hz period
    assert set(frames[0].markers) == {"zapesce", "srednji", "mali", "palac"}

    R0, _ = hand_frame_single(frames[0].markers["zapesce"],
                              frames[0].markers["srednji"], frames[0].markers["mali"])
    angles = []
    for fr in frames:
        R, _ = hand_frame_single(fr.markers["zapesce"], fr.markers["srednji"],
                                 fr.markers["mali"])
        angles.append(flexion_angle(R, R0))
    # Synthetic flexion swings +/-30 deg -> full peak-to-peak ~60 deg.
    assert np.degrees(np.ptp(angles)) > 45.0


def test_mock_bridge_over_udp():
    rx = UDPReceiver("127.0.0.1", 0, timeout=1.0)
    src = MockMarkerSource(rate_hz=240.0, realtime=True, noise_mm=0.0)
    th = threading.Thread(target=send_over_udp, args=(src, "127.0.0.1", rx.port),
                          daemon=True)
    th.start()
    time.sleep(0.05)
    got = [rx.receive_once() for _ in range(5)]
    rx.close()
    got = [f for f in got if f is not None]
    assert len(got) >= 3
    assert all("zapesce" in f.markers for f in got)
    assert [f.seq for f in got] == sorted(f.seq for f in got)  # monotonic


def test_mock_arm_emits_the_six_channels_as_scalars():
    """Same shape SDKArmSource sends, so --mode multi_joint can be rehearsed dry."""
    src = MockArmSource(rate_hz=120.0, realtime=False, noise_deg=0.0)
    frames = list(itertools.islice(iter(src), 600))
    assert set(frames[0].markers) == {
        "shoulder_yaw", "shoulder_pitch", "elbow",
        "wrist_flex", "wrist_dev", "wrist_axial"}
    # Each channel is a scalar carried in x, and must actually move.
    for ch in frames[0].markers:
        series = [f.markers[ch][0] for f in frames]
        assert all(f.markers[ch][1] == 0.0 and f.markers[ch][2] == 0.0 for f in frames)
        assert np.degrees(np.ptp(series)) > 10.0
