"""Safety guard: rate limiting, range clamping, fail-safe, e-stop."""

from __future__ import annotations

import math

from src.safety.guard import SafetyGuard


def _guard():
    return SafetyGuard(home=0.0, max_joint_speed_dps=40.0,
                       joint_range_dps=60.0, signal_timeout_s=0.15)


def test_rate_limit_bounds_step():
    g = _guard()
    dt = 1.0 / 125.0
    # Demand a huge jump; output may move at most max_speed*dt per step.
    d = g.step(math.radians(1000), dt, signal_age_s=0.0)
    assert d.rate_limited
    assert abs(d.angle) <= math.radians(40.0) * dt + 1e-9


def test_range_clamp_around_home():
    g = _guard()
    # Step many times toward a target far beyond the +/-60 deg range.
    last = 0.0
    for _ in range(2000):
        last = g.step(math.radians(200), 1.0 / 125.0).angle
    assert last <= math.radians(60.0) + 1e-6
    assert g.step(math.radians(200), 1.0 / 125.0).range_clamped


def test_fail_safe_on_stale_signal_holds():
    g = _guard()
    g.step(math.radians(10), 1.0 / 125.0, signal_age_s=0.0)
    held = g.last
    d = g.step(math.radians(50), 1.0 / 125.0, signal_age_s=0.5)  # stale
    assert d.halted
    assert d.angle == held  # frozen, no motion


def test_estop_freezes_output():
    g = _guard()
    g.step(math.radians(10), 1.0 / 125.0)
    held = g.last
    g.trip_estop()
    d = g.step(math.radians(50), 1.0 / 125.0)
    assert d.halted and d.angle == held
    g.reset_estop()
    assert not g.step(math.radians(10), 1.0 / 125.0).halted
