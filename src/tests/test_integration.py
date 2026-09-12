"""End-to-end dry-run: replay -> UDP -> angle -> filter -> safety -> dry sink.

Exercises the whole pipeline without a robot, on real recorded data.
"""

from __future__ import annotations

import csv
from pathlib import Path

from src.pipeline.main import load_config, run

REPO_ROOT = Path(__file__).resolve().parents[2]


def _cfg():
    cfg = load_config(REPO_ROOT / "src/config/default.yaml")
    cfg["robot"]["sink"] = "dry_run"
    cfg["udp"]["port"] = 0              # OS-assigned free port (avoids reserved ranges)
    cfg["source"]["loop"] = True
    return cfg


def test_pipeline_dry_run_end_to_end():
    summary = run(_cfg(), seconds=2.0)
    assert summary["latency"]["n"] > 100          # control loop ran
    assert summary["rx_received"] > 50            # frames flowed over UDP
    assert summary["rx_loss_pct"] < 50.0


def test_pipeline_with_packet_loss_stays_robust():
    cfg = _cfg()
    cfg["source"]["drop_rate"] = 0.2              # drop 20% of packets
    summary = run(cfg, seconds=2.0)
    # Loop must keep running and the receiver must observe the induced loss.
    assert summary["latency"]["n"] > 100
    assert summary["rx_lost"] > 0


def test_track_csv_records_angles_and_actual_state(tmp_path):
    """The gap that made earlier lab runs unusable: no angles were logged."""
    cfg = _cfg()
    track = tmp_path / "run.track.csv"
    cfg["logging"]["track_csv"] = str(track)
    cfg["logging"]["log_actual"] = True
    run(cfg, seconds=2.0)

    rows = list(csv.DictReader(track.open(encoding="utf-8")))
    assert len(rows) > 100
    j = cfg["mapping"]["joint_index"] + 1          # config is 0-based, columns are J1..J6
    assert f"in_J{j}_deg" in rows[0] and f"act_J{j}_deg" in rows[0]
    # The recorded human angle must actually vary -- a constant column would mean
    # the log is wired to the wrong place.
    values = [float(r[f"in_J{j}_deg"]) for r in rows]
    assert max(values) - min(values) > 1.0


def test_software_estop_freezes_the_output(tmp_path):
    cfg = _cfg()
    track = tmp_path / "estop.track.csv"
    cfg["logging"]["track_csv"] = str(track)
    cfg["control"]["estop_after_s"] = 1.0
    summary = run(cfg, seconds=2.0)

    j = cfg["mapping"]["joint_index"] + 1
    events = summary["safety_events"][f"J{j}"]
    assert events["halted_ticks"] > 50              # ~1 s of held output
    rows = list(csv.DictReader(track.open(encoding="utf-8")))
    held = [float(r[f"cmd_J{j}_deg"]) for r in rows if r[f"halted_J{j}"] == "1"]
    assert len(set(held)) == 1                      # frozen at one value


def test_added_latency_delays_the_command_path():
    cfg = _cfg()
    cfg["control"]["added_latency_ms"] = 120.0
    cfg["safety"]["signal_timeout_s"] = 0.6         # must exceed the injected delay
    summary = run(cfg, seconds=3.0)
    # Signal age (and hence measured latency) must reflect the injected delay.
    assert summary["latency"]["median_ms"] > 100.0
    assert summary["added_latency_ms"] == 120.0
