"""Golden tests for the OptiTrack CSV parser against the real recordings."""

from __future__ import annotations

import numpy as np

from src.optitrack.csv_loader import load_take
from .conftest import TAKE_V1


def test_v2_take_parses_with_four_markers(take_v2_path):
    take = load_take(take_v2_path)
    assert set(take.markers) == {"zapesce", "palac", "srednji", "mali"}
    assert take.frame_rate_hz == 120.0
    # Frame count must match the file metadata (validated inside load_take).
    assert take.n_frames > 1000
    for xyz in take.markers.values():
        assert xyz.shape == (take.n_frames, 3)
        assert not np.isnan(xyz).any()


def test_v2_time_monotonic_and_120hz(take_v2_path):
    take = load_take(take_v2_path)
    dt = np.diff(take.time_s)
    assert np.all(dt > 0)
    # Nominal 120 Hz -> ~8.33 ms spacing.
    assert abs(np.median(dt) - 1.0 / 120.0) < 1e-3


def test_v1_uses_dlan_and_srednjak_markers():
    # vjezbe_01 marker set differs: 'dlan' (not zapesce), 'srednjak' (not srednji).
    take = load_take(TAKE_V1, marker_names=("dlan", "palac", "srednjak", "mali"))
    assert set(take.markers) == {"dlan", "palac", "srednjak", "mali"}
    assert take.n_frames > 1000
    for xyz in take.markers.values():
        assert not np.isnan(xyz).any()


def test_first_row_matches_known_values():
    """Spot-check the first data row of vjezbe_02_x against known file content."""
    from .conftest import VJEZBE_02

    take = load_take(VJEZBE_02 / "hri_snimanje_vjezbe_02_x.csv")
    # From data/optitrack README / file: frame 0, zapesce XYZ.
    assert take.time_s[0] == 0.0
    np.testing.assert_allclose(
        take.markers["zapesce"][0], [114.962677, 1408.382446, -161.900131], rtol=0, atol=1e-3
    )


def test_track_replay_source():
    from pathlib import Path
    from src.optitrack.replay_source import TrackReplaySource

    track_file = Path("data/raw/lab_session_01092026_020000/telemetry/T-03.track.csv")
    if not track_file.exists():
        return

    source = TrackReplaySource(track_file, loop=False, realtime=False)
    assert len(source.frames) == 5625
    frames = list(source)
    assert len(frames) == 5625
    # Check that forward filling maintained continuous non-zero range for shoulder_yaw
    yaws = [np.degrees(f.markers["shoulder_yaw"][0]) for f in frames]
    assert min(yaws) < -40.0
    assert max(yaws) > 40.0
    # Hold frames shouldn't cause drops to 0 during peak motion
    peak_idx = int(np.argmax(np.abs(yaws)))
    around_peak = yaws[peak_idx - 5 : peak_idx + 5]
    assert all(abs(y) > 30.0 for y in around_peak)
