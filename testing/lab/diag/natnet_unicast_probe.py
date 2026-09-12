"""Validate live unicast NatNet transport using OUR (unit-tested) parsers.

Confirms the handshake mechanics learned from the SDK: send NAT_CONNECT, then a
periodic KEEPALIVE; in unicast Motive returns FRAMEOFDATA on the COMMAND socket.
Prints whether model-def arrived and how many frames in 4 s (expect ~480 @120Hz).

NOTE: on NatNet 4.0 our parse_model_def returns empty (version-specific layout) —
that is expected; use ``sdk_inspect.py`` for marker names. This probe only proves
the transport path works with our code.

Usage:
    python testing/lab/diag/natnet_unicast_probe.py <server_ip> <client_ip>
    # lab default: server=192.168.40.31  client=192.168.40.30
"""
import socket
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.optitrack.natnet import protocol as P  # noqa: E402

server = sys.argv[1] if len(sys.argv) > 1 else "192.168.40.31"
client = sys.argv[2] if len(sys.argv) > 2 else "192.168.40.30"
CMD_PORT = 1510


def connect_packet() -> bytes:
    body = bytearray(270)
    body[0:4] = b"Ping"
    body[265:269] = bytes([4, 5, 0, 0])     # NatNet version 4.5
    return struct.pack("<hh", P.NAT_CONNECT, len(body) + 1) + bytes(body) + b"\x00"


def simple_request(msg_id: int) -> bytes:
    return struct.pack("<hh", msg_id, 0) + b"\x00"


s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((client, 0))
s.settimeout(2.0)

print(f"UNICAST PROBE server={server} client={client} (bound {s.getsockname()})")
s.sendto(connect_packet(), (server, CMD_PORT))
s.sendto(simple_request(P.NAT_REQUEST_MODELDEF), (server, CMD_PORT))

model, frames, sample = None, 0, None
t0, last_ka = time.time(), 0.0
while time.time() - t0 < 4.0:
    now = time.time()
    if now - last_ka > 0.2:                  # keepalive sustains the unicast stream
        s.sendto(simple_request(P.NAT_KEEPALIVE), (server, CMD_PORT))
        last_ka = now
    try:
        data, _ = s.recvfrom(65535)
    except socket.timeout:
        continue
    mid, payload = P.unpack_message(data)
    if mid == P.NAT_MODELDEF and model is None:
        model = P.parse_model_def(payload)
    elif mid == P.NAT_FRAMEOFDATA:
        frames += 1
        if sample is None:
            fn, sets = P.parse_frame_marker_sets(payload)
            sample = [(n, len(p)) for n, p in sets]
            print(f"first FRAMEOFDATA #{fn}: sets={sample}")

print(f"RESULT: model_def_sets={len(model) if model else 0}  frames_in_4s={frames}")
print("OK transport" if frames > 100 else "NO/LOW FRAMES — provjeri Motive streaming/unicast")
s.close()
