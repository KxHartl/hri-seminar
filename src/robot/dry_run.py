"""Dry-run robot sink — no hardware, for offline pipeline testing.

Records every commanded joint angle and emulates control-period timing with a
busy-wait, so the pipeline (and its latency logging) can run end-to-end without
URSim or a real robot.
"""

from __future__ import annotations

import time

from .base import RobotSink

HOME_Q = [-1.6, -1.7, -2.2, -0.8, 1.6, 0.0]  # plausible UR3e home [rad]


class DryRunBackend(RobotSink):
    def __init__(self, control_hz: int = 125) -> None:
        self.control_hz = control_hz
        self.dt = 1.0 / control_hz
        self._home_q = list(HOME_Q)
        self.commands: list[float] = []
        self.q_commands: list[list[float]] = []
        self._last_q = list(HOME_Q)

    def connect(self) -> None:
        pass

    def get_home_q(self) -> list[float]:
        return list(self._home_q)

    def get_actual_q(self) -> list[float]:
        """Echo the last commanded pose (no hardware to lag behind it)."""
        return list(self._last_q)

    def init_period(self) -> float:
        return time.perf_counter()

    def servo_joint(self, joint_index: int, angle: float) -> None:
        self.commands.append(angle)
        self._last_q[joint_index] = angle

    def servo_q(self, q: list[float]) -> None:
        self.q_commands.append(list(q))
        self._last_q = list(q)

    def wait_period(self, t_start: float) -> None:
        remaining = self.dt - (time.perf_counter() - t_start)
        if remaining > 0:
            time.sleep(remaining)

    def stop(self) -> None:
        pass

    def disconnect(self) -> None:
        pass
