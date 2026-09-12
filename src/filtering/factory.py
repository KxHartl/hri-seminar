"""Build a uniform scalar filter callable ``f(x, t=None) -> y`` from config."""

from __future__ import annotations

from collections.abc import Callable

from .causal import ButterworthLowPass, ExponentialMovingAverage
from .one_euro import OneEuroFilter

Filter = Callable[..., float]


def make_filter(config: dict, fs_hz: float) -> Filter:
    """Return a filter callable from the ``filter`` config block.

    The returned callable always accepts ``(x, t=None)`` so the control loop can
    treat every filter kind uniformly.
    """
    kind = config.get("kind", "one_euro")

    if kind == "none":
        return lambda x, t=None: x

    if kind == "one_euro":
        p = config.get("one_euro", {})
        f = OneEuroFilter(freq_hz=fs_hz, min_cutoff=p.get("min_cutoff", 1.0),
                          beta=p.get("beta", 0.007), d_cutoff=p.get("d_cutoff", 1.0))
        return lambda x, t=None: f(x, t)

    if kind == "butterworth":
        p = config.get("butterworth", {})
        f = ButterworthLowPass(fs_hz=fs_hz, cutoff_hz=p.get("cutoff_hz", 6.0),
                               order=p.get("order", 2))
        return lambda x, t=None: f(x)

    if kind == "ema":
        p = config.get("ema", {})
        f = ExponentialMovingAverage(alpha=p.get("alpha", 0.2))
        return lambda x, t=None: f(x)

    raise ValueError(f"Nepoznat filter kind: {kind!r}")
