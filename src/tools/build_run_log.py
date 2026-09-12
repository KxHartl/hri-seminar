"""Build the session run log from the runs themselves.

``testing/lab/templates/run_log.csv`` was never filled in during the session, and
its planned parameters no longer describe what happened: every row says
``1dof_ur3`` while the whole matrix was executed in 6-DOF
(``pokreni_sve_testove.ps1``: "SVI TESTOVI RADE NA 6-DOF"). Rather than
reconstructing it by hand, this reads each run's own summaries so the log cannot
drift from the data again.

Per-run flags come from the runner script and are recorded here with it as the
source; everything else is read from ``*.summary.json`` and
``*.track.summary.json``.

Usage:
    python -m src.tools.build_run_log
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = REPO_ROOT / "data/raw/lab_session_01092026_020000/telemetry"
OUT = RESULTS_DIR / "run_log.csv"

JOINTS = [f"J{i}" for i in range(1, 7)]
FIDELITY = "scaled_input_to_actual"

# id, filter, added latency [ms], fail-safe threshold [ms], speed [deg/s],
# range [deg], video file, note.  Source: testing/lab/scripts/run_all_tests.ps1
PLANNED = [
    ("T-02", "one_euro", 0, 150, 150, 90, "T1a_natural_tempo.mp4", "vjernost 6-DOF, prirodni tempo"),
    ("T-03", "one_euro", 0, 150, 150, 90, "T1b_joint_walkthrough.mp4", "vjernost 6-DOF, prolaz po zglobovima"),
    ("T-04", "one_euro", 0, 150, 150, 90, "T2a_filter_one_euro.mp4", "filtri: One-Euro"),
    ("T-05", "none", 0, 150, 150, 90, "T2b_filter_none.mp4", "filtri: bez filtra"),
    ("T-06", "butterworth", 0, 150, 150, 90, "T2c_filter_butterworth.mp4", "filtri: Butterworth"),
    ("T-07", "ema", 0, 150, 150, 90, "T2d_filter_ema.mp4", "filtri: EMA"),
    ("T-08", "one_euro", 0, 150, 25, 90, "T3a_rate_limit.mp4", "sigurnost: rate-limit"),
    ("T-09", "one_euro", 0, 150, 150, 25, "T3b_range_limit.mp4", "sigurnost: range-limit"),
    ("T-10", "one_euro", 0, 150, 150, 90, "T3c_marker_occlusion.mp4", "sigurnost: okluzija markera"),
    ("T-12a", "one_euro", 0, 150, 150, 90, "T3d_estop.mp4", "sigurnost: e-stop (softverski 10s + teach pendant)"),
    ("T-20", "one_euro", 0, 150, 150, 90, "T6_step_response.mp4", "dinamika: 5 naglih pokreta (step response)"),
    ("T-13a", "one_euro", 0, 150, 150, 90, "T4a_latency_0ms.mp4", "latencija +0 ms"),
    ("T-13b", "one_euro", 50, 300, 150, 90, "T4b_latency_50ms.mp4", "latencija +50 ms"),
    ("T-13c", "one_euro", 100, 400, 150, 90, "T4c_latency_100ms.mp4", "latencija +100 ms"),
    ("T-13d", "one_euro", 200, 600, 150, 90, "T4d_latency_200ms.mp4", "latencija +200 ms"),
    ("T-13e", "one_euro", 400, 900, 150, 90, "T4e_latency_400ms.mp4", "latencija +400 ms"),
    ("T-14", "one_euro", 0, 150, 150, 90, "T5a_packet_loss_0pct.mp4", "gubitak 0 % (referenca)"),
    ("T-15", "one_euro", 0, 150, 150, 90, "T5b_packet_loss_5pct.mp4", "gubitak modeliran offline 5 %"),
    ("T-16", "one_euro", 0, 150, 150, 90, "T5c_packet_loss_10pct.mp4", "gubitak modeliran offline 10 %"),
    ("T-17", "one_euro", 0, 150, 150, 90, "T5d_packet_loss_20pct.mp4", "gubitak modeliran offline 20 %"),
    ("T-18", "one_euro", 0, 150, 150, 90, "T5e_packet_loss_30pct.mp4", "gubitak modeliran offline 30 %"),
    ("T-01", "", 0, 0, 0, 0, "", "NIJE IZVEDEN: URSim referenca"),
    ("T-11", "", 0, 0, 0, 0, "", "NIJE IZVEDEN: duplikat e-stop id-a u skripti"),
    ("T-19", "", 0, 0, 0, 0, "", "NIJE IZVEDEN: endurance 10 min"),
    ("T-21", "", 0, 0, 0, 0, "", "NIJE IZVEDEN: ponovljivost T-02"),
]

HEADER = [
    "id", "izvedeno", "filter", "trajanje_s", "takt_hz", "ulaz_hz", "hold_pct",
    "dodana_lat_ms", "prag_ms", "brzina_dps", "raspon_deg",
    "lat_median_ms", "lat_p95_ms", "lat_p99_ms", "lat_jitter_ms", "rx_loss_pct",
    "rmse_mean_deg", "rmse_poravnato_deg", "lag_j3_ms",
    "ratelim_ticks", "rangeclamp_ticks", "halted_ticks", "video", "napomena",
]


def _read(stem: str) -> tuple[dict | None, dict | None]:
    net = RESULTS_DIR / f"{stem}.summary.json"
    trk = RESULTS_DIR / f"{stem}.track.summary.json"
    return (
        json.loads(net.read_text(encoding="utf-8")) if net.exists() else None,
        json.loads(trk.read_text(encoding="utf-8")) if trk.exists() else None,
    )


def _mean(trk: dict, field: str) -> str:
    vals = [trk["joints"][j][FIDELITY][field] for j in JOINTS
            if j in trk["joints"] and FIDELITY in trk["joints"][j]]
    vals = [v for v in vals if not math.isnan(v)]
    return f"{sum(vals) / len(vals):.2f}" if vals else ""


def _sum_flag(trk: dict, flag: str) -> int:
    return sum(trk["joints"][j]["safety_events"].get(flag, 0)
               for j in JOINTS if j in trk["joints"])


def build() -> int:
    rows = []
    for stem, filt, added, timeout, speed, rng, video, note in PLANNED:
        net, trk = _read(stem)
        row = {k: "" for k in HEADER}
        row.update(id=stem, filter=filt, video=video, napomena=note,
                   izvedeno="da" if (net or video) else "ne")
        if added or timeout:
            row.update(dodana_lat_ms=added, prag_ms=timeout,
                       brzina_dps=speed, raspon_deg=rng)
        if net:
            lat = net["latency"]
            row.update(
                lat_median_ms=f"{lat['median_ms']:.2f}",
                lat_p95_ms=f"{lat['p95_ms']:.2f}",
                lat_p99_ms=f"{lat['p99_ms']:.2f}",
                lat_jitter_ms=f"{lat['jitter_ms']:.2f}",
                rx_loss_pct=f"{net.get('rx_loss_pct', 0.0):.2f}",
            )
        if trk:
            j3 = trk["joints"].get("J3", {})
            lag = j3.get(FIDELITY, {}).get("lag_ms", float("nan"))
            row.update(
                trajanje_s=f"{trk['duration_s']:.1f}",
                takt_hz=f"{trk['effective_rate_hz']:.1f}",
                ulaz_hz=f"{j3.get('input_update_rate_hz', '')}",
                hold_pct=f"{j3.get('hold_pct', '')}",
                rmse_mean_deg=_mean(trk, "rmse_deg"),
                rmse_poravnato_deg=_mean(trk, "rmse_aligned_deg"),
                lag_j3_ms="" if math.isnan(lag) else f"{lag:.0f}",
                ratelim_ticks=_sum_flag(trk, "ratelim_ticks"),
                rangeclamp_ticks=_sum_flag(trk, "rangeclamp_ticks"),
                halted_ticks=_sum_flag(trk, "halted_ticks"),
            )
        rows.append(row)

    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=HEADER)
        w.writeheader()
        w.writerows(rows)
    done = sum(1 for r in rows if r["izvedeno"] == "da")
    print(f"{OUT} -- {done}/{len(rows)} izvedenih runova")
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
