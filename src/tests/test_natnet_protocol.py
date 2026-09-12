"""Round-trip tests for the NatNet decoder (build -> parse)."""

from __future__ import annotations

import numpy as np

from src.optitrack.natnet import protocol as P


def test_message_framing_round_trip():
    payload = b"\x01\x02\x03\x04"
    msg_id, body = P.unpack_message(P.pack_message(P.NAT_FRAMEOFDATA, payload))
    assert msg_id == P.NAT_FRAMEOFDATA
    assert body == payload


def test_model_def_round_trip():
    sets = [
        ("MarkerSet 001", ["zapesce", "palac", "srednji", "mali"]),
        ("all", ["m1", "m2"]),
    ]
    out = P.parse_model_def(P.build_model_def(sets))
    assert out == sets


def test_model_def_stops_at_non_markerset():
    # A MarkerSet followed by a rigid-body (type 1) dataset: parsing must stop
    # cleanly after the MarkerSet (we don't decode version-specific datasets).
    import struct
    payload = bytearray(struct.pack("<i", 2))                 # 2 datasets
    payload += struct.pack("<i", 0)                            # type 0 = markerset
    payload += b"hand\x00" + struct.pack("<i", 1) + b"zapesce\x00"
    payload += struct.pack("<i", 1)                            # type 1 = rigid body
    payload += b"\xff" * 8                                     # arbitrary tail
    sets = P.parse_model_def(bytes(payload))
    assert sets == [("hand", ["zapesce"])]


def test_frame_marker_sets_round_trip():
    pts = np.array([[0.1, 1.4, -0.16], [0.13, 1.37, -0.04]])
    frame_no, sets = P.parse_frame_marker_sets(
        P.build_frame_marker_sets(42, [("MarkerSet 001", pts)]))
    assert frame_no == 42
    assert sets[0][0] == "MarkerSet 001"
    np.testing.assert_allclose(sets[0][1], pts, atol=1e-6)


def test_frame_empty_marker_set():
    frame_no, sets = P.parse_frame_marker_sets(
        P.build_frame_marker_sets(1, [("empty", np.zeros((0, 3)))]))
    assert sets[0][1].shape == (0, 3)
