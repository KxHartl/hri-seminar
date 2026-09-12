"""Angle logging, artificial delay and the measured-state hook.

These cover the gap that made earlier lab runs unusable for fidelity analysis:
the runs recorded timing only, so input-vs-output could never be reconstructed.
"""

from __future__ import annotations

import csv
import math

from src.pipeline.delay import DelayLine
from src.pipeline.tracklog import JointSample, TrackLog
from src.robot.dry_run import DryRunBackend

DEG = math.radians(1.0)


def _log(**kw) -> TrackLog:
    return TrackLog(joints=(2,), home_q=(0.0, 0.0, 1.0, 0.0, 0.0, 0.0), **kw)


def test_columns_use_one_based_joint_names():
    # Joint index 2 (0-based, the elbow) must appear as J3, the paper's naming.
    header = _log().header()
    assert header[:2] == ["t_s", "t_capture"]
    assert "in_J3_deg" in header and "cmd_J3_deg" in header
    assert "act_J3_deg" not in header          # only with log_actual
    assert "in_J2_deg" not in header


def test_actual_column_only_when_requested():
    assert "act_J3_deg" in _log(log_actual=True).header()


def test_angles_written_in_degrees_relative_to_home(tmp_path):
    tl = _log(log_actual=True)
    # target/command are absolute [rad]; home for J3 is 1.0 rad.
    tl.record(0.0, 100.0, {2: JointSample(raw=10 * DEG, filtered=9 * DEG,
                                          target=1.0 + 5 * DEG,
                                          command=1.0 + 4 * DEG)},
              actual_q=[0, 0, 1.0 + 3 * DEG, 0, 0, 0])
    p = tmp_path / "t.csv"
    tl.to_csv(p)
    row = next(iter(csv.DictReader(p.open(encoding="utf-8"))))
    assert float(row["in_J3_deg"]) == 10.0
    assert float(row["filt_J3_deg"]) == 9.0
    assert float(row["target_J3_deg"]) == 5.0     # home-relative, not 58.3
    assert float(row["cmd_J3_deg"]) == 4.0
    assert float(row["act_J3_deg"]) == 3.0


def test_safety_flags_are_counted():
    tl = _log()
    s_plain = JointSample(0.0, 0.0, 1.0, 1.0)
    s_flagged = JointSample(0.0, 0.0, 1.0, 1.0, rate_limited=True, halted=True)
    tl.record(0.0, 0.0, {2: s_plain})
    tl.record(0.1, 0.0, {2: s_flagged})
    tl.record(0.2, 0.0, {2: s_flagged})
    counts = tl.summary()["joints"]["J3"]
    assert counts["ratelim_ticks"] == 2
    assert counts["halted_ticks"] == 2
    assert counts["rangeclamp_ticks"] == 0


def test_decimation_keeps_every_nth_tick():
    tl = _log(decimate=3)
    for i in range(10):
        tl.record(i * 0.1, 0.0, {2: JointSample(0.0, 0.0, 1.0, 1.0)})
    assert len(tl.rows) == 4          # ticks 0, 3, 6, 9


def test_due_matches_which_ticks_are_kept():
    # The loop uses .due to skip reading the robot's state on discarded ticks,
    # so it must agree exactly with what record() keeps.
    tl = _log(decimate=3)
    kept = []
    for i in range(9):
        if tl.due:
            kept.append(i)
        tl.record(i * 0.1, 0.0, {2: JointSample(0.0, 0.0, 1.0, 1.0)})
    assert kept == [0, 3, 6]
    assert len(tl.rows) == 3


def test_missing_joint_sample_does_not_break_the_row(tmp_path):
    tl = _log()
    tl.record(0.0, 0.0, {})           # e.g. a channel absent from the frame
    p = tmp_path / "t.csv"
    tl.to_csv(p)
    rows = list(csv.DictReader(p.open(encoding="utf-8")))
    assert len(rows) == 1
    assert float(rows[0]["cmd_J3_deg"]) == 0.0


# --- artificial delay ------------------------------------------------------

def test_delay_line_holds_frames_back_then_releases_them():
    d = DelayLine(0.1)
    assert d.push_and_get(0.00, "f0", 0.001) == (None, float("inf"))
    assert d.push_and_get(0.05, "f1", 0.001) == (None, float("inf"))
    frame, age = d.push_and_get(0.11, "f2", 0.001)
    assert frame == "f0"
    # Reported age must include the time spent waiting -- the command really is
    # based on data that old, which is why the fail-safe timeout must be raised.
    assert age == 0.001 + 0.11


def test_zero_delay_is_a_passthrough():
    assert DelayLine(0.0).push_and_get(1.0, "x", 0.5) == ("x", 0.5)


# --- measured robot state --------------------------------------------------

def test_dry_run_reports_last_commanded_pose_as_actual():
    b = DryRunBackend()
    home = b.get_home_q()
    assert b.get_actual_q() == home
    b.servo_joint(2, 0.42)
    assert b.get_actual_q()[2] == 0.42
    b.servo_q([0.1] * 6)
    assert b.get_actual_q() == [0.1] * 6
