"""Minimal NatNet client: request model definitions, stream frame data.

NOTE: the socket handshake/subscription cannot be tested without a live Motive
server. The decoding it relies on IS unit-tested (``protocol.py``). Verify the
connection details in the lab: NatNet version, multicast vs unicast, the
multicast group/ports, and the local client NIC IP. Defaults match Motive's
out-of-the-box settings.
"""

from __future__ import annotations

import logging
import socket
from collections.abc import Iterator

from . import protocol as P

log = logging.getLogger(__name__)

DEFAULT_MULTICAST = "239.255.42.99"
DEFAULT_COMMAND_PORT = 1510
DEFAULT_DATA_PORT = 1511


class NatNetClient:
    def __init__(
        self,
        server_ip: str,
        client_ip: str = "0.0.0.0",
        use_multicast: bool = True,
        multicast_group: str = DEFAULT_MULTICAST,
        command_port: int = DEFAULT_COMMAND_PORT,
        data_port: int = DEFAULT_DATA_PORT,
        timeout: float = 2.0,
    ) -> None:
        self.server_ip = server_ip
        self.client_ip = client_ip
        self.use_multicast = use_multicast
        self.multicast_group = multicast_group
        self.command_port = command_port
        self.data_port = data_port
        self.timeout = timeout
        self._cmd: socket.socket | None = None
        self._data: socket.socket | None = None

    def connect(self) -> None:
        self._cmd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._cmd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._cmd.bind((self.client_ip, 0))
        self._cmd.settimeout(self.timeout)

        self._data = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._data.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if self.use_multicast:
            self._data.bind(("", self.data_port))
            mreq = (socket.inet_aton(self.multicast_group)
                    + socket.inet_aton(self.client_ip if self.client_ip != "0.0.0.0"
                                       else "0.0.0.0"))
            self._data.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        else:
            self._data.bind((self.client_ip, self.data_port))
        self._data.settimeout(self.timeout)
        log.info("NatNet spojen: server=%s multicast=%s data_port=%d",
                 self.server_ip, self.use_multicast, self.data_port)

    def request_model_def(self, retries: int = 3) -> list[tuple[str, list[str]]]:
        """Ask the server for model definitions; return parsed marker sets."""
        assert self._cmd is not None
        req = P.pack_message(P.NAT_REQUEST_MODELDEF)
        for _ in range(retries):
            self._cmd.sendto(req, (self.server_ip, self.command_port))
            try:
                for _ in range(20):  # skip serverinfo/other responses
                    data, _addr = self._cmd.recvfrom(65535)
                    msg_id, payload = P.unpack_message(data)
                    if msg_id == P.NAT_MODELDEF:
                        return P.parse_model_def(payload)
            except socket.timeout:
                continue
        raise TimeoutError("NatNet: nema MODELDEF odgovora (provjeri vezu/postavke)")

    def frames(self) -> Iterator[tuple[int, list[tuple[str, "object"]]]]:
        """Yield (frame_number, marker_sets) from streamed FRAMEOFDATA packets."""
        assert self._data is not None
        while True:
            try:
                data, _addr = self._data.recvfrom(65535)
            except socket.timeout:
                continue
            msg_id, payload = P.unpack_message(data)
            if msg_id == P.NAT_FRAMEOFDATA:
                yield P.parse_frame_marker_sets(payload)

    def close(self) -> None:
        for s in (self._cmd, self._data):
            if s is not None:
                s.close()
        self._cmd = self._data = None
