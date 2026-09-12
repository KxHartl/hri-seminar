"""Robot sinks: URSim / real UR3e via RTDE, plus a dry-run backend."""

from __future__ import annotations

from .base import RobotSink
from .dry_run import DryRunBackend


def make_sink(kind: str, ip: str, control_hz: int = 125,
              lookahead_time: float = 0.1, gain: int = 300) -> RobotSink:
    """Factory: 'ursim' | 'ur3e' | 'dry_run'."""
    if kind == "dry_run":
        return DryRunBackend(control_hz=control_hz)
    from .rtde_backend import RTDEBackend  # imported lazily (needs ur_rtde)
    return RTDEBackend(ip=ip, control_hz=control_hz,
                       lookahead_time=lookahead_time, gain=gain, variant=kind)
