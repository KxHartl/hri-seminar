"""Per-tick logging of the joint angles themselves (input vs. command vs. actual).

The latency log (:mod:`src.pipeline.latency`) answers *how fast* a sample reaches
the robot. It cannot answer *how faithfully* the robot reproduces the arm, because
it records no angles at all -- which is exactly why tracking fidelity (RMSE, lag)
could not be computed from earlier lab runs.

This log closes that gap. Every control tick it stores, per driven joint:

  * ``in``      -- the raw human angle straight from OptiTrack (pre-filter),
  * ``filt``    -- after the causal filter,
  * ``target``  -- after gain/offset mapping, before the safety layer,
  * ``cmd``     -- what the safety layer actually commanded,
  * ``act``     -- what the robot is really at (optional; RTDE ``getActualQ``),
  * the three :class:`~src.safety.guard.SafetyDecision` flags, so a run *proves*
    that rate limiting / range clamping / fail-safe hold engaged rather than
    merely existing in the source.

Angles are written in **degrees relative to the home pose** (matching the periodic
console log in the pipeline) and columns use the paper's **1-based J1..J6**
naming, while the joint indices passed in stay 0-based as everywhere in the code.

Rows are buffered in memory and written once at the end of the run: the control
loop must never block on disk I/O.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple

RAD2DEG = 180.0 / math.pi

# Per-joint column groups, in the order they are written.
_ANGLE_COLS = ("in", "filt", "target", "cmd")
_FLAG_COLS = ("ratelim", "rangeclamp", "halted")


class JointSample(NamedTuple):
    """One joint's state for one control tick. Angles are absolute [rad]."""

    raw: float          # human angle, pre-filter (already home-relative)
    filtered: float     # after the causal filter (home-relative)
    target: float       # mapped joint target, pre-safety (absolute)
    command: float      # post-safety commanded joint angle (absolute)
    rate_limited: bool = False
    range_clamped: bool = False
    halted: bool = False


@dataclass
class TrackLog:
    """Collects per-joint angle samples per control step.

    Args:
        joints: 0-based indices of the joints being driven, in column order.
        home_q: home pose [rad]; commanded/actual angles are logged relative to it.
        log_actual: also write the robot's measured angle (``act_J*_deg``).
        decimate: keep every N-th tick (1 = every tick). Long endurance runs at
            125 Hz produce 75k rows for 10 minutes, so this keeps files sane.
    """

    joints: tuple[int, ...]
    home_q: tuple[float, ...]
    log_actual: bool = False
    decimate: int = 1
    rows: list[tuple] = field(default_factory=list)
    _tick: int = 0

    def __post_init__(self) -> None:
        self.joints = tuple(int(j) for j in self.joints)
        self.home_q = tuple(float(q) for q in self.home_q)
        self.decimate = max(1, int(self.decimate))

    # -- recording -------------------------------------------------------

    @property
    def due(self) -> bool:
        """Whether the *next* :meth:`record` call will be kept, not decimated away.

        Lets the control loop skip the cost of reading the robot's measured state
        on ticks that would be discarded anyway -- so ``--track-decimate N`` also
        divides the per-tick RTDE read cost by N.
        """
        return self._tick % self.decimate == 0

    def record(
        self,
        t_s: float,
        t_capture: float,
        samples: dict[int, JointSample],
        actual_q: list[float] | None = None,
    ) -> None:
        """Append one tick. ``samples`` is keyed by 0-based joint index."""
        self._tick += 1
        if (self._tick - 1) % self.decimate:
            return
        row: list[float] = [t_s, t_capture]
        for j in self.joints:
            s = samples.get(j)
            home = self.home_q[j] if j < len(self.home_q) else 0.0
            if s is None:
                row += [0.0, 0.0, 0.0, 0.0]
                if self.log_actual:
                    row.append(0.0)
                row += [0, 0, 0]
                continue
            row += [
                s.raw * RAD2DEG,
                s.filtered * RAD2DEG,
                (s.target - home) * RAD2DEG,
                (s.command - home) * RAD2DEG,
            ]
            if self.log_actual:
                act = actual_q[j] if actual_q is not None and j < len(actual_q) else home
                row.append((act - home) * RAD2DEG)
            row += [int(s.rate_limited), int(s.range_clamped), int(s.halted)]
        self.rows.append(tuple(row))

    # -- output ----------------------------------------------------------

    def header(self) -> list[str]:
        cols = ["t_s", "t_capture"]
        for j in self.joints:
            jn = j + 1                      # paper convention: J1..J6
            cols += [f"{c}_J{jn}_deg" for c in _ANGLE_COLS]
            if self.log_actual:
                cols.append(f"act_J{jn}_deg")
            cols += [f"{c}_J{jn}" for c in _FLAG_COLS]
        return cols

    def summary(self) -> dict:
        """Per-joint counts of ticks on which each safety layer engaged."""
        out: dict = {"n": len(self.rows), "decimate": self.decimate,
                     "log_actual": self.log_actual, "joints": {}}
        if not self.rows:
            return out
        header = self.header()
        for j in self.joints:
            jn = j + 1
            counts = {}
            for flag in _FLAG_COLS:
                idx = header.index(f"{flag}_J{jn}")
                counts[f"{flag}_ticks"] = sum(int(r[idx]) for r in self.rows)
            out["joints"][f"J{jn}"] = counts
        return out

    def to_csv(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        header = self.header()
        n_flags = len(_FLAG_COLS)
        with path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(header)
            for row in self.rows:
                out = [f"{row[0]:.6f}", f"{row[1]:.6f}"]
                # Angles get 4 decimals; the trailing flags stay integers.
                per_joint = (len(header) - 2) // max(1, len(self.joints))
                i = 2
                for _ in self.joints:
                    n_ang = per_joint - n_flags
                    out += [f"{row[i + k]:.4f}" for k in range(n_ang)]
                    out += [str(int(row[i + n_ang + k])) for k in range(n_flags)]
                    i += per_joint
                w.writerow(out)
