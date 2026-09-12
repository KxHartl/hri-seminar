"""NatNet wire format: message framing, model-def + frame-of-data decoding.

Only the version-stable parts are decoded:
  * MODELDEF dataset type 0 (MarkerSet description: set name + ordered marker names),
  * FRAMEOFDATA MarkerSets section (set name + marker positions, in metres).

Parsing stops at the first non-MarkerSet model-def dataset (their byte sizes are
version-specific); MarkerSets always come first, which is all we need to name the
hand markers. Builders are provided so the decoder can be round-trip tested
without Motive.
"""

from __future__ import annotations

import struct

import numpy as np

# Message IDs (subset).
NAT_CONNECT = 0
NAT_SERVERINFO = 1
NAT_REQUEST_MODELDEF = 4
NAT_MODELDEF = 5
NAT_REQUEST_FRAMEOFDATA = 6
NAT_FRAMEOFDATA = 7
NAT_KEEPALIVE = 10

_HDR = struct.Struct("<HH")     # message_id, payload_size
_DESC_MARKERSET = 0


class _Reader:
    """Little-endian sequential reader over a bytes payload."""

    def __init__(self, data: bytes, offset: int = 0) -> None:
        self.d = data
        self.o = offset

    def i32(self) -> int:
        v = struct.unpack_from("<i", self.d, self.o)[0]
        self.o += 4
        return v

    def f32(self) -> float:
        v = struct.unpack_from("<f", self.d, self.o)[0]
        self.o += 4
        return v

    def string(self) -> str:
        end = self.d.index(b"\x00", self.o)
        s = self.d[self.o:end].decode("utf-8", errors="replace")
        self.o = end + 1
        return s


# ---------------------------------------------------------------- framing ----

def pack_message(msg_id: int, payload: bytes = b"") -> bytes:
    return _HDR.pack(msg_id, len(payload)) + payload


def unpack_message(data: bytes) -> tuple[int, bytes]:
    """Return (message_id, payload). Tolerates trailing bytes."""
    msg_id, size = _HDR.unpack_from(data, 0)
    return msg_id, data[4:4 + size] if size else data[4:]


# ------------------------------------------------------------- model def -----

def parse_model_def(payload: bytes) -> list[tuple[str, list[str]]]:
    """Parse MODELDEF; return [(marker_set_name, [marker_names...]), ...]."""
    r = _Reader(payload)
    n_datasets = r.i32()
    sets: list[tuple[str, list[str]]] = []
    for _ in range(n_datasets):
        dtype = r.i32()
        if dtype != _DESC_MARKERSET:
            break  # later dataset types are version-specific; MarkerSets come first
        name = r.string()
        n_markers = r.i32()
        names = [r.string() for _ in range(n_markers)]
        sets.append((name, names))
    return sets


# --------------------------------------------------------- frame of data -----

def parse_frame_marker_sets(payload: bytes) -> tuple[int, list[tuple[str, np.ndarray]]]:
    """Parse the MarkerSets section of FRAMEOFDATA.

    Returns (frame_number, [(set_name, positions (n,3) in metres), ...]).
    """
    r = _Reader(payload)
    frame_number = r.i32()
    n_sets = r.i32()
    sets: list[tuple[str, np.ndarray]] = []
    for _ in range(n_sets):
        name = r.string()
        n = r.i32()
        pts = np.array([[r.f32(), r.f32(), r.f32()] for _ in range(n)], dtype=float)
        if pts.size == 0:
            pts = pts.reshape(0, 3)
        sets.append((name, pts))
    return frame_number, sets


# ----------------------------------------------- builders (for testing) ------

def build_model_def(sets: list[tuple[str, list[str]]]) -> bytes:
    b = bytearray(struct.pack("<i", len(sets)))
    for name, names in sets:
        b += struct.pack("<i", _DESC_MARKERSET)
        b += name.encode("utf-8") + b"\x00"
        b += struct.pack("<i", len(names))
        for nm in names:
            b += nm.encode("utf-8") + b"\x00"
    return bytes(b)


def build_frame_marker_sets(frame_number: int,
                            sets: list[tuple[str, np.ndarray]]) -> bytes:
    b = bytearray(struct.pack("<i", frame_number))
    b += struct.pack("<i", len(sets))
    for name, pts in sets:
        b += name.encode("utf-8") + b"\x00"
        b += struct.pack("<i", len(pts))
        for p in pts:
            b += struct.pack("<3f", float(p[0]), float(p[1]), float(p[2]))
    return bytes(b)
