"""Robot sink interface — drives a single joint via a servo loop."""

from __future__ import annotations

from abc import ABC, abstractmethod


class RobotSink(ABC):
    """Abstract robot sink. Backends: URSim/UR3e (RTDE) or dry-run.

    The pipeline only ever sets one joint angle per control step; the backend
    keeps the other joints at their home values.
    """

    control_hz: int

    @abstractmethod
    def connect(self) -> None:
        ...

    @abstractmethod
    def get_home_q(self) -> list[float]:
        """Return the joint vector captured at connect time (home pose)."""

    @abstractmethod
    def get_actual_q(self) -> list[float]:
        """Return the joint vector the robot is *actually* at right now [rad].

        Distinct from the commanded value: comparing the two is what makes
        tracking fidelity (input -> real motion) measurable rather than assumed.
        """

    @abstractmethod
    def init_period(self) -> float:
        """Mark the start of a control period; returns a start timestamp."""

    @abstractmethod
    def servo_joint(self, joint_index: int, angle: float) -> None:
        """Command one joint to ``angle`` [rad] for the current control step."""

    @abstractmethod
    def servo_q(self, q: list[float]) -> None:
        """Command the full 6-joint vector ``q`` [rad] for the current control step.

        Used by the multi-joint (full-arm) control mode; ``servo_joint`` remains
        for the single-joint mode.
        """

    @abstractmethod
    def wait_period(self, t_start: float) -> None:
        """Sleep so the control step lasts exactly 1/control_hz."""

    @abstractmethod
    def stop(self) -> None:
        """Stop servo motion (controlled)."""

    @abstractmethod
    def disconnect(self) -> None:
        ...

    def __enter__(self) -> "RobotSink":
        self.connect()
        return self

    def __exit__(self, *exc) -> None:
        try:
            self.stop()
        finally:
            self.disconnect()
