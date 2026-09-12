"""RTDE backend for URSim and the real UR3e (identical ur_rtde API).

Switching URSim <-> UR3e is only a config change (sink kind + IP). Uses
``servoJ`` with the controller's own period timing (``initPeriod``/``waitPeriod``)
for deterministic, low-jitter joint streaming — the right interface for
real-time control (vs. the URScript-over-secondary-interface + ``time.sleep``
approach in the course exercise).
"""

from __future__ import annotations

import logging

from .base import RobotSink

log = logging.getLogger(__name__)


class RTDEBackend(RobotSink):
    def __init__(
        self,
        ip: str,
        control_hz: int = 125,
        lookahead_time: float = 0.1,
        gain: int = 300,
        variant: str = "ursim",
    ) -> None:
        self.ip = ip
        self.control_hz = control_hz
        self.dt = 1.0 / control_hz
        self.lookahead_time = lookahead_time
        self.gain = gain
        self.variant = variant
        self._rc = None  # RTDEControlInterface
        self._rr = None  # RTDEReceiveInterface
        self._home_q: list[float] = []

    def connect(self) -> None:
        import rtde_control
        import rtde_receive

        log.info("RTDE connect %s (%s) ...", self.ip, self.variant)
        self._rr = rtde_receive.RTDEReceiveInterface(self.ip)
        self._home_q = list(self._rr.getActualQ())
        # Frequency MUST be passed: without it ur_rtde paces initPeriod/waitPeriod at
        # the controller maximum — 125 Hz on CB3 but 500 Hz on e-Series. The safety
        # layer rate-limits with dt = 1/control_hz, so a faster tick would silently
        # loosen the speed limit by the ratio (4x on a UR3e). Measured in lab
        # 2026-08-31 on the UR3e: 500 Hz loop against an 8 ms dt.
        self._rc = rtde_control.RTDEControlInterface(self.ip, float(self.control_hz))
        log.info("RTDE povezan. home_q=%s", [round(q, 3) for q in self._home_q])

    def get_home_q(self) -> list[float]:
        return list(self._home_q)

    def get_actual_q(self) -> list[float]:
        # The receive interface is already connected (see connect()), so this is
        # a local read of the latest RTDE frame -- no extra connection cost.
        return list(self._rr.getActualQ())

    def init_period(self) -> float:
        return self._rc.initPeriod()

    def servo_joint(self, joint_index: int, angle: float) -> None:
        q = list(self._home_q)
        q[joint_index] = angle
        # servoJ(q, speed, acceleration, time, lookahead_time, gain)
        self._rc.servoJ(q, 0.0, 0.0, self.dt, self.lookahead_time, self.gain)

    def servo_q(self, q: list[float]) -> None:
        # servoJ(q, speed, acceleration, time, lookahead_time, gain)
        self._rc.servoJ(list(q), 0.0, 0.0, self.dt, self.lookahead_time, self.gain)

    def move_j(self, q: list[float], speed: float = 0.3,
               acceleration: float = 0.5) -> None:
        """Blocking moveJ to ``q`` [rad] — used to restore the reference pose.

        Deliberately slow (0.3 rad/s): this runs with people around, and the
        move can span a large angle if the robot drifted during earlier runs.
        """
        self._rc.moveJ(list(q), speed, acceleration)

    def wait_period(self, t_start: float) -> None:
        self._rc.waitPeriod(t_start)

    def stop(self) -> None:
        if self._rc is not None:
            self._rc.servoStop()

    def disconnect(self) -> None:
        if self._rc is not None:
            self._rc.stopScript()
            self._rc.disconnect()
            self._rc = None
        if self._rr is not None:
            self._rr.disconnect()
            self._rr = None
