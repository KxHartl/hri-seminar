"""UDP wire-format round-trip."""

from __future__ import annotations

import numpy as np

from src.optitrack.base import MarkerFrame
from src.optitrack import protocol


def test_encode_decode_round_trip():
    frame = MarkerFrame(
        seq=12345,
        t_capture=1.2345678,
        markers={
            "zapesce": np.array([114.962677, 1408.382446, -161.900131]),
            "srednji": np.array([133.05, 1377.74, -39.27]),
            "mali": np.array([89.09, 1383.93, -77.17]),
        },
    )
    out = protocol.decode(protocol.encode(frame))
    assert out.seq == frame.seq
    assert abs(out.t_capture - frame.t_capture) < 1e-9
    assert set(out.markers) == set(frame.markers)
    for k in frame.markers:
        np.testing.assert_allclose(out.markers[k], frame.markers[k], rtol=0, atol=1e-3)


def test_decode_rejects_garbage():
    import pytest
    with pytest.raises(ValueError):
        protocol.decode(b"not-a-valid-packet-xxxxxxx")
