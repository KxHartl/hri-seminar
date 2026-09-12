"""Artificial end-to-end delay, for probing how latency degrades control.

The measured path (UDP -> RTDE, all on one machine) sits at ~4 ms median, which
leaves nothing to compare against: without a knob to *increase* latency there is
no way to measure how much delay the mapping tolerates before tracking falls
apart. This inserts a controlled delay ahead of the safety layer, so the guard
still protects the robot while the operator experiences a slower system.

The reported signal age deliberately includes the injected delay -- the command
really is based on data that old. Consequently the fail-safe timeout
(``safety.signal_timeout_s``) must be raised above the injected delay for a
sweep, otherwise the guard holds permanently and measures nothing.
"""

from __future__ import annotations

from collections import deque


class DelayLine:
    """Holds marker frames back by ``delay_s`` before the control loop sees them."""

    def __init__(self, delay_s: float) -> None:
        self.delay_s = max(0.0, float(delay_s))
        self._buf: deque[tuple[float, object, float]] = deque()

    def push_and_get(self, now: float, frame, age: float):
        """Feed the newest frame in, get back the one delayed by ``delay_s``.

        Returns ``(frame, age)`` with ``age`` grown by the time the frame spent
        waiting here, or ``(None, inf)`` while the line is still filling.
        """
        if self.delay_s <= 0.0:
            return frame, age
        if frame is not None:
            self._buf.append((now, frame, age))

        cutoff = now - self.delay_s
        released = None
        while self._buf and self._buf[0][0] <= cutoff:
            released = self._buf.popleft()
        if released is None:
            return None, float("inf")
        t_push, out_frame, out_age = released
        return out_frame, out_age + (now - t_push)
