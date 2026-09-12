"""Offline comparison of the streaming filters on a real angle series.

Quantifies the lag<->smoothing trade-off central to the seminar: each causal
filter's jitter reduction and its delay (estimated by cross-correlation), with
the non-causal Savitzky-Golay filter included only as an offline "ideal"
reference (it is unusable in real time — ~1-2 s lag).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import savgol_filter

from .causal import ButterworthLowPass, ExponentialMovingAverage
from .one_euro import OneEuroFilter


@dataclass
class FilterMetrics:
    name: str
    jitter_reduction_pct: float   # 1 - jitter(out)/jitter(raw), in %
    lag_ms: float                 # estimated group delay
    rms_vs_raw_deg: float         # RMS difference from raw (smoothing strength)


def _jitter(x: np.ndarray) -> float:
    return float(np.std(np.diff(x)))


def _estimate_lag_ms(raw: np.ndarray, out: np.ndarray, fs: float,
                     max_lag_s: float = 1.0) -> float:
    """Cross-correlation delay of ``out`` behind ``raw``, in milliseconds.

    Two properties matter here, and the first version of this function had
    neither.

    The search window is given in **seconds**, not samples, so it means the same
    thing at every sampling rate. And the shift is picked by the strongest
    *absolute* correlation, so a channel the mapping inverts (``arm_mapping``
    sets ``invert: true`` on shoulder pitch and wrist flex) reports its real
    delay instead of an arbitrary one.

    Returns ``nan`` when the best shift lands on the edge of the window: the true
    optimum is then outside it, and the number would describe ``max_lag_s``
    rather than the signals. The lab summaries carried a constant 481.5 ms for
    exactly that reason — 60 samples at 124.6 Hz, the old hard-coded bound.
    """
    n = len(raw)
    if fs <= 0 or n != len(out) or n < 12:
        return float("nan")
    max_lag = min(max(1, int(round(max_lag_s * fs))), n - 11)
    raw0 = raw - raw.mean()
    out0 = out - out.mean()
    if not np.any(raw0) or not np.any(out0):
        return float("nan")
    best_k, best_c = -1, -np.inf
    for k in range(max_lag + 1):
        a = out0[k:]
        b = raw0[: n - k] if k else raw0
        if len(a) <= 10 or not np.any(a) or not np.any(b):
            continue
        c = abs(float(np.corrcoef(a, b)[0, 1]))
        if c > best_c:
            best_c, best_k = c, k
    if best_k < 0 or best_k >= max_lag:
        return float("nan")
    return best_k / fs * 1e3


# Public alias: the same cross-correlation lag estimate is what track_analysis
# needs to measure input -> commanded/actual delay on a live run.
estimate_lag_ms = _estimate_lag_ms


def compare(angle_rad: np.ndarray, fs_hz: float,
            one_euro_params: dict | None = None) -> list[FilterMetrics]:
    """Run the streaming filters (+ savgol reference) and return metrics."""
    deg = np.degrees(angle_rad)
    p = one_euro_params or {"min_cutoff": 1.0, "beta": 0.007}
    dt = np.arange(len(deg)) / fs_hz

    runs: dict[str, np.ndarray] = {}

    oe = OneEuroFilter(freq_hz=fs_hz, **p)
    runs["one_euro"] = np.array([oe(x, t) for x, t in zip(deg, dt)])

    bw = ButterworthLowPass(fs_hz=fs_hz, cutoff_hz=6.0, order=2)
    runs["butterworth"] = np.array([bw(x) for x in deg])

    ema = ExponentialMovingAverage(alpha=0.2)
    runs["ema"] = np.array([ema(x) for x in deg])

    win = min(251, len(deg) - (1 - len(deg) % 2))
    if win >= 5:
        runs["savgol (offline ref)"] = savgol_filter(deg, win, 3)

    raw_j = _jitter(deg)
    out = []
    for name, sig in runs.items():
        out.append(FilterMetrics(
            name=name,
            jitter_reduction_pct=100.0 * (1.0 - _jitter(sig) / raw_j) if raw_j else 0.0,
            lag_ms=_estimate_lag_ms(deg, sig, fs_hz),
            rms_vs_raw_deg=float(np.sqrt(np.mean((sig - deg) ** 2))),
        ))
    return out
