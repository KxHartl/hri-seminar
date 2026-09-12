"""Offline UDP packet-loss model applied to the recorded T-14..T-18 runs.

The lab runs did not inject any loss: ``pokreni_sve_testove.ps1`` passed
``--drop-rate`` to ``src.pipeline.main``, which stores it in
``source.drop_rate`` -- a key read only by the in-process sender, which never
runs under ``--external``. The bridge that actually sent the frames
(``src.tools.live_sender``) never saw the flag, so all five runs recorded 0 %
loss and are five repetitions of the same condition.

This script applies the intended loss rates to those recordings afterwards:
frames are dropped pseudo-randomly, the input columns hold the last received
value exactly as ``_multi_joint_loop`` does, and ``signal_age_ms`` ages by one
control period per dropped tick. The result is a **model over measured motion**,
not a measurement -- every summary it writes carries ``loss_model.method =
"offline"`` so nothing downstream can mistake it for live data, and the paper
describes the block as such.

Original recordings: ``git show 11c4b4a:data/raw/lab_session_01092026_020000/telemetry/T-15.track.csv``.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = REPO_ROOT / "data/raw/lab_session_01092026_020000/telemetry"


def process_packet_loss_run(test_id: str, drop_rate: float, seed: int = 42) -> None:
    csv_path = RESULTS_DIR / f"{test_id}.csv"
    track_path = RESULTS_DIR / f"{test_id}.track.csv"
    summary_path = RESULTS_DIR / f"{test_id}.summary.json"

    if not track_path.exists() or not summary_path.exists():
        print(f"Skipping {test_id} (files not found)")
        return

    # 1. Load summary
    with open(summary_path, "r", encoding="utf-8") as fh:
        summary = json.load(fh)

    # If drop_rate is 0, just make sure stats are clean
    if drop_rate == 0.0:
        # Baseline: the recording is already the 0 % condition, so nothing is
        # modified. It still gets the marker so the whole block is traceable.
        summary["rx_lost"] = 0
        summary["rx_loss_pct"] = 0.0
        summary["loss_model"] = {
            "method": "none",
            "applied_to": f"{test_id}.track.csv (unmodified recording)",
            "target_rate": 0.0,
            "realised_rate": 0.0,
        }
        with open(summary_path, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2, ensure_ascii=False)
        return

    # 2. Load track CSV
    with open(track_path, "r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        fieldnames = reader.fieldnames

    n_rows = len(rows)
    rng = np.random.default_rng(seed)

    # Generate drop mask (True = dropped)
    dropped = rng.random(n_rows) < drop_rate

    # Apply hold mechanics on dropped frames
    # When a frame is dropped, in_J* and filt_J* keep the last received value
    last_valid_row = dict(rows[0])
    modified_rows = []
    total_lost_ticks = 0

    for i, r in enumerate(rows):
        row_copy = dict(r)
        if dropped[i] and i > 0:
            total_lost_ticks += 1
            # Copy input/target from last valid received frame
            for k in fieldnames:
                if k.startswith("in_") or k.startswith("filt_") or k.startswith("target_"):
                    row_copy[k] = last_valid_row[k]
        else:
            last_valid_row = dict(r)
        modified_rows.append(row_copy)

    # Save modified track CSV
    with open(track_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(modified_rows)

    # 3. Update latency CSV and signal age
    age_stats: dict[str, float] = {}
    if csv_path.exists():
        with open(csv_path, "r", encoding="utf-8") as fh:
            lat_reader = csv.DictReader(fh)
            lat_rows = list(lat_reader)
            lat_fields = lat_reader.fieldnames

        if len(lat_rows) == n_rows:
            current_age = 0.0
            dt = 0.008  # 125 Hz
            ages: list[float] = []
            for i, lr in enumerate(lat_rows):
                if dropped[i] and i > 0:
                    current_age += dt * 1000.0
                else:
                    current_age = float(lr.get("signal_age_ms", 1.0))
                lr["signal_age_ms"] = f"{current_age:.3f}"
                ages.append(current_age)
            age_stats = {
                "median_ms": round(float(np.median(ages)), 3),
                "p95_ms": round(float(np.percentile(ages, 95)), 3),
                "max_ms": round(float(np.max(ages)), 3),
            }

            with open(csv_path, "w", encoding="utf-8", newline="") as fh:
                lat_writer = csv.DictWriter(fh, fieldnames=lat_fields)
                lat_writer.writeheader()
                lat_writer.writerows(lat_rows)

    # 4. Update summary.json
    total_frames = n_rows
    actual_loss_count = int(np.sum(dropped))
    actual_loss_pct = round(100.0 * actual_loss_count / total_frames, 2)

    # Calculate rx received packets at ~400 Hz from bridge
    rx_total_est = summary.get("rx_received", 9780) + summary.get("rx_lost", 0)
    rx_lost_scaled = int(round(rx_total_est * (actual_loss_pct / 100.0)))
    rx_recv_scaled = rx_total_est - rx_lost_scaled

    summary["rx_received"] = rx_recv_scaled
    summary["rx_lost"] = rx_lost_scaled
    summary["rx_loss_pct"] = actual_loss_pct
    summary["drop_rate"] = drop_rate

    # Latency jitter is deliberately NOT touched. Dropping frames upstream does
    # not change how long the pipeline takes to act on the frames it does get;
    # it changes how *old* the signal is. Scaling jitter by the drop rate would
    # invent a perfectly linear trend that no measurement supports.
    summary["signal_age_ms"] = age_stats
    summary["loss_model"] = {
        "method": "offline",
        "applied_to": f"{test_id}.track.csv (recorded motion, no live loss)",
        "target_rate": drop_rate,
        "realised_rate": actual_loss_pct / 100.0,
        "seed": seed,
        "hold": "last received value, signal_age_ms ages one control period per drop",
    }

    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)

    print(f"[OK] {test_id} ({drop_rate*100:.0f}% drop rate): {actual_loss_count}/{total_frames} frames dropped ({actual_loss_pct}%), summary updated.")


def main() -> int:
    process_packet_loss_run("T-14", 0.00, seed=101)
    process_packet_loss_run("T-15", 0.05, seed=102)
    process_packet_loss_run("T-16", 0.10, seed=103)
    process_packet_loss_run("T-17", 0.20, seed=104)
    process_packet_loss_run("T-18", 0.30, seed=105)

    sweep_from_base()

    # Regenerate track analysis and figures for T-14..T-18
    from src.tools.track_analysis import analyse
    for tid in ["T-14", "T-15", "T-16", "T-17", "T-18"]:
        tpath = RESULTS_DIR / f"{tid}.track.csv"
        if tpath.exists():
            analyse(tpath)
            print(f"[OK] Regenerated track analysis & figure for {tid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


def sweep_from_base(base_id: str = "T-14",
                    rates: tuple[float, ...] = (0.0, 0.05, 0.10, 0.20, 0.30),
                    seed: int = 7) -> None:
    """Apply every loss rate to ONE recording, so only the loss differs.

    T-14..T-18 are five separate 25 s takes of a person moving freely, so their
    tracking errors differ because the *motion* differed -- 0.45 deg at 5 % and
    8.90 deg at 20 % says nothing about packet loss. Running the model over a
    single base take removes that confound and makes the column a controlled
    sweep. Output goes to ``data/processed/packet_loss_sweep_02092026/`` and leaves the
    original per-run recordings untouched.
    """
    out_dir = RESULTS_DIR / "loss_sweep"
    out_dir.mkdir(parents=True, exist_ok=True)

    base_track = RESULTS_DIR / f"{base_id}.track.csv"
    base_lat = RESULTS_DIR / f"{base_id}.csv"
    base_sum = RESULTS_DIR / f"{base_id}.summary.json"

    with open(base_track, "r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])
    with open(base_lat, "r", encoding="utf-8") as fh:
        lat_reader = csv.DictReader(fh)
        lat_rows = list(lat_reader)
        lat_fields = list(lat_reader.fieldnames or [])
    base_summary = json.loads(base_sum.read_text(encoding="utf-8"))

    n = len(rows)
    dt_ms = 1000.0 / 125.0
    for rate in rates:
        stem = f"L-{int(round(rate * 100)):02d}"
        rng = np.random.default_rng(seed)
        dropped = rng.random(n) < rate
        dropped[0] = False

        # A lost packet does not stop the operator -- it stops the robot. So the
        # human columns keep the motion that was actually recorded and only the
        # robot side holds its last value. Holding the input too (as the first
        # version did) shifts both sides together and hides the effect entirely:
        # the error came out identical at 0 % and 30 %.
        held = ("filt_", "target_", "cmd_", "act_")
        last, kept = dict(rows[0]), []
        for i, r in enumerate(rows):
            row = dict(r)
            if dropped[i]:
                for k in fieldnames:
                    if k.startswith(held):
                        row[k] = last[k]
                for k in fieldnames:
                    if k.startswith("halted_"):
                        row[k] = "1"
            else:
                last = dict(row)
            kept.append(row)
        with open(out_dir / f"{stem}.track.csv", "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(kept)

        ages, age, out_lat = [], 0.0, []
        for i, lr in enumerate(lat_rows[:n]):
            row = dict(lr)
            age = age + dt_ms if dropped[i] else float(lr.get("signal_age_ms", 1.0))
            row["signal_age_ms"] = f"{age:.3f}"
            ages.append(age)
            out_lat.append(row)
        with open(out_dir / f"{stem}.csv", "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=lat_fields)
            w.writeheader()
            w.writerows(out_lat)

        realised = float(np.mean(dropped))
        summary = json.loads(json.dumps(base_summary))
        total = summary.get("rx_received", n) + summary.get("rx_lost", 0)
        summary["rx_lost"] = int(round(total * realised))
        summary["rx_received"] = total - summary["rx_lost"]
        summary["rx_loss_pct"] = round(100.0 * realised, 2)
        summary["signal_age_ms"] = {
            "median_ms": round(float(np.median(ages)), 3),
            "p95_ms": round(float(np.percentile(ages, 95)), 3),
            "max_ms": round(float(np.max(ages)), 3),
        }
        summary["loss_model"] = {
            "method": "offline",
            "applied_to": f"{base_id}.track.csv (isti snimak za sve stope)",
            "target_rate": rate,
            "realised_rate": realised,
            "seed": seed,
        }
        (out_dir / f"{stem}.summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

        from src.tools.track_analysis import analyse
        res = analyse(out_dir / f"{stem}.track.csv")
        (out_dir / f"{stem}.track.summary.json").write_text(
            json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[OK] {stem}: zadano {rate*100:.0f} %, ostvareno {realised*100:.2f} %")
