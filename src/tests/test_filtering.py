"""Sanity + behavioural tests for the streaming filters."""

from __future__ import annotations

import numpy as np

from src.filtering.one_euro import OneEuroFilter
from src.filtering.causal import ButterworthLowPass, ExponentialMovingAverage, MovingAverage
from src.filtering.analysis import estimate_lag_ms

FS = 120.0


def _noisy_sine(n=1200, f=0.5, noise=0.05, seed=0):
    rng = np.random.default_rng(seed)
    t = np.arange(n) / FS
    clean = np.sin(2 * np.pi * f * t)
    return t, clean, clean + rng.normal(0, noise, n)


def _jitter(x):
    """Sample-to-sample jitter: std of first difference (lag-independent)."""
    return np.std(np.diff(x))


def _max_lagged_corr(a, b, max_lag=20):
    """Best Pearson correlation of ``a`` vs ``b`` over small time shifts.

    Lag-tolerant: a causal filter preserves the signal shape but adds delay, so
    we accept a small shift here and quantify the lag itself separately (Stage 4).
    """
    best = -1.0
    for k in range(max_lag + 1):
        a_s, b_s = (a[k:], b[:len(b) - k]) if k else (a, b)
        if len(a_s) > 10:
            best = max(best, np.corrcoef(a_s, b_s)[0, 1])
    return best


def test_one_euro_reduces_jitter_and_tracks():
    t, clean, noisy = _noisy_sine()
    f = OneEuroFilter(freq_hz=FS, min_cutoff=1.0, beta=0.007)
    out = np.array([f(x, ti) for x, ti in zip(noisy, t)])
    # Smoothing: the filtered signal is far less jittery than the raw input...
    assert _jitter(out[100:]) < 0.5 * _jitter(noisy[100:])
    # ...while preserving the underlying motion's shape (lag-tolerant correlation).
    assert _max_lagged_corr(out[100:], clean[100:]) > 0.99


def test_one_euro_passes_constant():
    f = OneEuroFilter(freq_hz=FS)
    out = [f(3.0, i / FS) for i in range(50)]
    assert abs(out[-1] - 3.0) < 1e-6


def test_butterworth_smooths():
    t, clean, noisy = _noisy_sine()
    bw = ButterworthLowPass(fs_hz=FS, cutoff_hz=4.0, order=2)
    out = np.array([bw(x) for x in noisy])
    assert _jitter(out[100:]) < 0.5 * _jitter(noisy[100:])


def test_ema_and_moving_average_pass_constant():
    ema = ExponentialMovingAverage(alpha=0.2)
    ma = MovingAverage(window=5)
    for _ in range(50):
        y_ema = ema(2.5)
        y_ma = ma(2.5)
    assert abs(y_ema - 2.5) < 1e-6
    assert abs(y_ma - 2.5) < 1e-9


# --- lag estimator -------------------------------------------------------
# The lab summaries reported a constant 481.5 ms because the old estimator
# searched a hard-coded 60-sample window and returned its edge. These pin the
# three properties that fix: a real shift is recovered, an inverted signal is
# handled, and an out-of-window shift is refused instead of guessed.

def _ramp_burst(n=1500, seed=3):
    rng = np.random.default_rng(seed)
    t = np.arange(n) / FS
    return np.sin(2 * np.pi * 0.3 * t) + 0.02 * rng.standard_normal(n)


def test_estimate_lag_recovers_known_shift():
    x = _ramp_burst()
    shift = 25                                   # samples -> 208.3 ms at 120 Hz
    delayed = np.concatenate([np.full(shift, x[0]), x[:-shift]])
    lag = estimate_lag_ms(x, delayed, FS)
    assert abs(lag - shift / FS * 1e3) < 1e3 / FS * 2


def test_estimate_lag_handles_inverted_channel():
    x = _ramp_burst(seed=4)
    shift = 12
    delayed = -np.concatenate([np.full(shift, x[0]), x[:-shift]])
    lag = estimate_lag_ms(x, delayed, FS)
    assert abs(lag - shift / FS * 1e3) < 1e3 / FS * 2


def test_estimate_lag_refuses_edge_of_window():
    x = _ramp_burst(seed=5)
    shift = 60
    delayed = np.concatenate([np.full(shift, x[0]), x[:-shift]])
    lag = estimate_lag_ms(x, delayed, FS, max_lag_s=shift / FS)
    assert np.isnan(lag), "shift on the window edge must not be reported as a value"
