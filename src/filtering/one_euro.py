"""One-Euro filter (Casiez, Roussel, Vogel, ACM CHI 2012).

Adaptive low-pass for noisy interactive signals: low lag at low speed, strong
smoothing when the signal is slow/noisy. Causal and O(1) per sample, so it suits
real-time streaming. Chosen as the primary filter (lit. justification:
``TASK/LITERATURE.md`` — plain low-pass adds phase lag unfit for real-time).
"""

from __future__ import annotations

import math


def _alpha(cutoff_hz: float, dt: float) -> float:
    tau = 1.0 / (2.0 * math.pi * cutoff_hz)
    return 1.0 / (1.0 + tau / dt)


class OneEuroFilter:
    """Scalar One-Euro filter.

    Args:
        freq_hz: nominal sample rate (used when no per-sample timestamp given).
        min_cutoff: minimum cutoff frequency [Hz] (more smoothing when small).
        beta: speed coefficient (higher -> less lag on fast motion).
        d_cutoff: cutoff for the derivative low-pass [Hz].
    """

    def __init__(
        self,
        freq_hz: float = 120.0,
        min_cutoff: float = 1.0,
        beta: float = 0.007,
        d_cutoff: float = 1.0,
    ) -> None:
        self.freq_hz = float(freq_hz)
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)
        self._x_prev: float | None = None
        self._dx_prev: float = 0.0
        self._t_prev: float | None = None

    def reset(self) -> None:
        self._x_prev = None
        self._dx_prev = 0.0
        self._t_prev = None

    def __call__(self, x: float, t: float | None = None) -> float:
        """Filter one sample. ``t`` is an optional timestamp [s]."""
        if self._x_prev is None:
            self._x_prev = x
            self._t_prev = t
            return x

        if t is not None and self._t_prev is not None:
            dt = t - self._t_prev
            dt = dt if dt > 1e-6 else 1.0 / self.freq_hz
        else:
            dt = 1.0 / self.freq_hz

        dx = (x - self._x_prev) / dt
        a_d = _alpha(self.d_cutoff, dt)
        dx_hat = a_d * dx + (1.0 - a_d) * self._dx_prev

        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        a = _alpha(cutoff, dt)
        x_hat = a * x + (1.0 - a) * self._x_prev

        self._x_prev = x_hat
        self._dx_prev = dx_hat
        self._t_prev = t
        return x_hat
