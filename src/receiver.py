"""UDP receiver for marker frames: loss/reorder detection + rate statistics.

Provides two access patterns:
  * :class:`UDPReceiver` — blocking iterator yielding frames, updating stats.
  * :class:`BackgroundReceiver` — a thread holding the *latest* frame, so the
    control loop can pull at its own rate and detect signal loss (staleness)
    for the fail-safe.
"""

from __future__ import annotations

import logging
import socket
import threading
import time
from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass, field

from .optitrack import protocol
from .optitrack.base import MarkerFrame

log = logging.getLogger(__name__)


@dataclass
class ReceiverStats:
    received: int = 0
    lost: int = 0                 # gaps inferred from sequence numbers
    reordered: int = 0            # frames arriving with seq <= last max
    duplicates: int = 0
    _max_seq: int = -1
    _seen: set[int] = field(default_factory=set)
    _arrivals: deque[float] = field(default_factory=lambda: deque(maxlen=512))

    def update(self, seq: int, t_wall: float) -> None:
        self._arrivals.append(t_wall)
        if seq in self._seen:
            self.duplicates += 1
            return
        self._seen.add(seq)
        self.received += 1
        if self._max_seq < 0:
            self._max_seq = seq
            return
        if seq > self._max_seq + 1:
            self.lost += seq - (self._max_seq + 1)
        if seq <= self._max_seq:
            self.reordered += 1
        else:
            self._max_seq = seq

    @property
    def rate_hz(self) -> float:
        if len(self._arrivals) < 2:
            return 0.0
        span = self._arrivals[-1] - self._arrivals[0]
        return (len(self._arrivals) - 1) / span if span > 0 else 0.0

    @property
    def interarrival_jitter_ms(self) -> float:
        if len(self._arrivals) < 3:
            return 0.0
        dts = [(b - a) * 1e3 for a, b in zip(self._arrivals, list(self._arrivals)[1:])]
        mean = sum(dts) / len(dts)
        var = sum((d - mean) ** 2 for d in dts) / len(dts)
        return var ** 0.5

    @property
    def loss_pct(self) -> float:
        total = self.received + self.lost
        return 100.0 * self.lost / total if total else 0.0


class UDPReceiver:
    """Blocking UDP receiver. Iterate to get frames; inspect ``.stats``."""

    def __init__(self, host: str, port: int, timeout: float | None = 1.0,
                 bufsize: int = 2048) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))
        # If port==0 the OS assigns a free one; expose the actual bound port.
        self.port = self.sock.getsockname()[1]
        self.timeout = timeout
        if timeout is not None:
            self.sock.settimeout(timeout)
        self.bufsize = bufsize
        self.stats = ReceiverStats()

    def receive_once(self) -> MarkerFrame | None:
        """Receive and decode one datagram. Returns None on timeout."""
        try:
            data, _ = self.sock.recvfrom(self.bufsize)
        except socket.timeout:
            return None
        frame = protocol.decode(data)
        self.stats.update(frame.seq, time.perf_counter())
        return frame

    def receive_latest(self) -> MarkerFrame | None:
        """Block for one datagram, then drain any backlog and return the newest.

        Critical for real-time: if this thread is briefly starved, the OS socket
        buffer accumulates frames; serving the *newest* (discarding the backlog)
        keeps the control loop on fresh data instead of replaying stale samples.
        """
        frame = self.receive_once()
        if frame is None:
            return None
        self.sock.setblocking(False)
        try:
            while True:
                try:
                    data, _ = self.sock.recvfrom(self.bufsize)
                except (BlockingIOError, OSError):
                    break
                frame = protocol.decode(data)
                self.stats.update(frame.seq, time.perf_counter())
        finally:
            self.sock.settimeout(self.timeout)
        return frame

    def __iter__(self) -> Iterator[MarkerFrame]:
        while True:
            frame = self.receive_once()
            if frame is not None:
                yield frame

    def close(self) -> None:
        self.sock.close()


class BackgroundReceiver:
    """Threaded receiver holding the most recent frame for the control loop."""

    def __init__(self, host: str, port: int) -> None:
        self._rx = UDPReceiver(host, port, timeout=0.5)
        self._latest: MarkerFrame | None = None
        self._latest_wall: float = 0.0
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="udp-rx", daemon=True)

    @property
    def port(self) -> int:
        return self._rx.port

    @property
    def stats(self) -> ReceiverStats:
        return self._rx.stats

    def start(self) -> "BackgroundReceiver":
        self._thread.start()
        return self

    def _run(self) -> None:
        rx = self._rx
        while not self._stop.is_set():
            frame = rx.receive_latest()   # drain to newest, never serve stale backlog
            if frame is not None:
                with self._lock:
                    self._latest = frame
                    self._latest_wall = time.perf_counter()

    def get_latest(self) -> tuple[MarkerFrame | None, float]:
        """Return (latest_frame, age_seconds). age is inf if nothing received."""
        with self._lock:
            if self._latest is None:
                return None, float("inf")
            return self._latest, time.perf_counter() - self._latest_wall

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=1.0)
        self._rx.close()
