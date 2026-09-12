"""Multi-layer safety guard for the single-joint command stream.

Layers (applied in order, every control step):
  1. e-stop / fail-safe  — if tripped or the signal is stale, freeze output.
  2. range clamp         — keep the joint within +/- range of the home angle.
  3. rate limit          — bound |delta| per step by max joint speed.

Thresholds come from config (``TASK/LITERATURE.md`` motivates the values:
ISO/TS 15066 reduced-speed logic; latency-based fail-safe timeout).
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class SafetyDecision:
    angle: float          # safe joint angle to command [rad]
    rate_limited: bool
    range_clamped: bool
    halted: bool          # e-stop or fail-safe active -> output frozen


class SafetyGuard:
    """Stateful guard around a single joint angle [rad]."""

    def __init__(
        self,
        home: float,
        max_joint_speed_dps: float = 40.0,
        joint_range_dps: float = 60.0,
        signal_timeout_s: float = 0.15,
    ) -> None:
        self.home = home
        self.max_speed = math.radians(max_joint_speed_dps)   # rad/s
        self.half_range = math.radians(joint_range_dps)        # rad
        self.signal_timeout_s = signal_timeout_s
        self._last = home
        self._estop = False

    @property
    def last(self) -> float:
        return self._last

    def trip_estop(self) -> None:
        self._estop = True

    def reset_estop(self) -> None:
        self._estop = False

    def step(self, target: float, dt: float, signal_age_s: float = 0.0) -> SafetyDecision:
        """Filter one target angle through all safety layers."""
        halted = self._estop or signal_age_s > self.signal_timeout_s
        if halted:
            # Fail-safe: hold the last commanded angle (no motion).
            return SafetyDecision(self._last, False, False, True)

        # Range clamp around home.
        lo, hi = self.home - self.half_range, self.home + self.half_range
        clamped = min(max(target, lo), hi)
        range_clamped = clamped != target

        # Rate limit.
        max_step = self.max_speed * max(dt, 1e-4)
        delta = clamped - self._last
        rate_limited = abs(delta) > max_step
        if rate_limited:
            clamped = self._last + math.copysign(max_step, delta)

        self._last = clamped
        return SafetyDecision(clamped, rate_limited, range_clamped, False)
