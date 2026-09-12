"""Causal baseline filters for comparison against the One-Euro filter.

All are streaming (one sample in, one sample out) so they are valid in real time,
unlike the non-causal Savitzky-Golay used offline in the course exercise.
"""

from __future__ import annotations

from collections import deque

import numpy as np
from scipy.signal import butter, sosfilt, sosfilt_zi


class ButterworthLowPass:
    """Streaming 2nd-order (default) Butterworth low-pass via second-order sections."""

    def __init__(self, fs_hz: float, cutoff_hz: float = 6.0, order: int = 2) -> None:
        self.sos = butter(order, cutoff_hz, btype="low", fs=fs_hz, output="sos")
        self._zi: np.ndarray | None = None

    def reset(self) -> None:
        self._zi = None

    def __call__(self, x: float) -> float:
        if self._zi is None:
            self._zi = sosfilt_zi(self.sos) * x
        y, self._zi = sosfilt(self.sos, [x], zi=self._zi)
        return float(y[0])


class ExponentialMovingAverage:
    """First-order IIR EMA: ``y[n] = a*x[n] + (1-a)*y[n-1]``."""

    def __init__(self, alpha: float = 0.2) -> None:
        self.alpha = float(alpha)
        self._y: float | None = None

    def reset(self) -> None:
        self._y = None

    def __call__(self, x: float) -> float:
        if self._y is None:
            self._y = x
        else:
            self._y = self.alpha * x + (1.0 - self.alpha) * self._y
        return self._y


class MovingAverage:
    """Causal sliding-window mean (introduces ~window/2 samples of lag)."""

    def __init__(self, window: int = 5) -> None:
        self.window = int(window)
        self._buf: deque[float] = deque(maxlen=self.window)

    def reset(self) -> None:
        self._buf.clear()

    def __call__(self, x: float) -> float:
        self._buf.append(x)
        return float(np.mean(self._buf))
