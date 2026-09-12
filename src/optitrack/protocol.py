"""Compact, self-describing UDP wire format for marker frames.

Layout (little-endian)::

    magic   2s   b'OT'
    version B    1
    seq     I    uint32 sequence number
    t       d    float64 capture time [s]
    n       B    marker count
    repeated n times:
        namelen B
        name    <namelen>s  (utf-8)
        x,y,z   3f   float32 position [mm]

Self-describing (carries marker names) so the receiver is robust to marker-set
changes; the per-frame overhead is negligible at 120 Hz with ~4 markers.
"""

from __future__ import annotations

import struct

import numpy as np

from .base import MarkerFrame

_MAGIC = b"OT"
_VERSION = 1
_HEADER = struct.Struct("<2sB I d B")
_XYZ = struct.Struct("<3f")


def encode(frame: MarkerFrame) -> bytes:
    out = bytearray(_HEADER.pack(_MAGIC, _VERSION, frame.seq & 0xFFFFFFFF,
                                 frame.t_capture, len(frame.markers)))
    for name, xyz in frame.markers.items():
        nb = name.encode("utf-8")
        out.append(len(nb))
        out += nb
        out += _XYZ.pack(float(xyz[0]), float(xyz[1]), float(xyz[2]))
    return bytes(out)


def decode(data: bytes) -> MarkerFrame:
    magic, version, seq, t, n = _HEADER.unpack_from(data, 0)
    if magic != _MAGIC or version != _VERSION:
        raise ValueError(f"Neispravan paket: magic={magic!r} version={version}")
    off = _HEADER.size
    markers: dict[str, np.ndarray] = {}
    for _ in range(n):
        namelen = data[off]
        off += 1
        name = data[off:off + namelen].decode("utf-8")
        off += namelen
        x, y, z = _XYZ.unpack_from(data, off)
        off += _XYZ.size
        markers[name] = np.array([x, y, z], dtype=float)
    return MarkerFrame(seq=seq, t_capture=t, markers=markers)
