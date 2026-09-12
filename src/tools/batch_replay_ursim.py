"""Batch runner to replay recorded laboratory telemetry runs against the URSim simulator.

Executes each test through the full real-time pipeline (TrackReplaySource -> UDP ->
Filter -> SafetyGuard -> URSim RTDE), logs latency and tracking data, and produces
comparative metrics against the physical robot runs.
"""

from __future__ import annotations

import argparse
import logging
import math
import subprocess
import sys
import time
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data/raw/lab_session_01092026_020000/telemetry"
DEFAULT_OUT_DIR = REPO_ROOT / "data/processed/sim_comparison_04092026"

log = logging.getLogger("batch_replay")

# All 21 executed laboratory tests with their parameters matching run_all_tests.ps1
TEST_DEFINITIONS = [
    # 1. 6-DOF tracking fidelity
    {"id": "T-02", "name": "6-DOF prirodni tempo", "seconds": 46.0, "range_dps": 90.0, "max_speed_dps": 150.0},
    {"id": "T-03", "name": "6-DOF prolaz zglob-po-zglob", "seconds": 46.0, "range_dps": 90.0, "max_speed_dps": 150.0},

    # 2. Filter comparison
    {"id": "T-04", "name": "Filtar: One-Euro", "seconds": 31.0, "filter": "one_euro", "range_dps": 90.0, "max_speed_dps": 150.0},
    {"id": "T-05", "name": "Filtar: Bez filtriranja (none)", "seconds": 31.0, "filter": "none", "range_dps": 90.0, "max_speed_dps": 150.0},
    {"id": "T-06", "name": "Filtar: Butterworth", "seconds": 31.0, "filter": "butterworth", "range_dps": 90.0, "max_speed_dps": 150.0},
    {"id": "T-07", "name": "Filtar: EMA", "seconds": 34.0, "filter": "ema", "range_dps": 90.0, "max_speed_dps": 150.0},

    # 3. Safety mechanisms
    {"id": "T-08", "name": "Sigurnost: Rate-limit (25 deg/s)", "seconds": 26.0, "filter": "one_euro", "range_dps": 90.0, "max_speed_dps": 25.0},
    {"id": "T-09", "name": "Sigurnost: Range-limit (±25 deg)", "seconds": 26.0, "filter": "one_euro", "range_dps": 25.0, "max_speed_dps": 150.0},
    {"id": "T-10", "name": "Sigurnost: Okluzija markera", "seconds": 31.0, "filter": "one_euro", "range_dps": 90.0, "max_speed_dps": 150.0},
    {"id": "T-12a", "name": "Sigurnost: Softverski E-stop", "seconds": 21.0, "filter": "one_euro", "range_dps": 90.0, "max_speed_dps": 150.0, "estop_after": 10.0},
    {"id": "T-20", "name": "Dinamika: 5 naglih pokreta", "seconds": 31.0, "filter": "one_euro", "range_dps": 90.0, "max_speed_dps": 150.0},

    # 4. Latency impact sweep
    {"id": "T-13a", "name": "Latencija: +0 ms", "seconds": 31.0, "filter": "one_euro", "range_dps": 90.0, "max_speed_dps": 150.0, "added_latency_ms": 0.0, "signal_timeout_s": 0.15},
    {"id": "T-13b", "name": "Latencija: +50 ms", "seconds": 31.0, "filter": "one_euro", "range_dps": 90.0, "max_speed_dps": 150.0, "added_latency_ms": 50.0, "signal_timeout_s": 0.30},
    {"id": "T-13c", "name": "Latencija: +100 ms", "seconds": 31.0, "filter": "one_euro", "range_dps": 90.0, "max_speed_dps": 150.0, "added_latency_ms": 100.0, "signal_timeout_s": 0.40},
    {"id": "T-13d", "name": "Latencija: +200 ms", "seconds": 31.0, "filter": "one_euro", "range_dps": 90.0, "max_speed_dps": 150.0, "added_latency_ms": 200.0, "signal_timeout_s": 0.60},
    {"id": "T-13e", "name": "Latencija: +400 ms", "seconds": 31.0, "filter": "one_euro", "range_dps": 90.0, "max_speed_dps": 150.0, "added_latency_ms": 400.0, "signal_timeout_s": 0.90},

    # 5. Packet loss sweep
    {"id": "T-14", "name": "Gubitak paketa: 0%", "seconds": 26.0, "filter": "one_euro", "range_dps": 90.0, "max_speed_dps": 150.0, "drop_rate": 0.0},
    {"id": "T-15", "name": "Gubitak paketa: 5%", "seconds": 26.0, "filter": "one_euro", "range_dps": 90.0, "max_speed_dps": 150.0, "drop_rate": 0.05},
    {"id": "T-16", "name": "Gubitak paketa: 10%", "seconds": 26.0, "filter": "one_euro", "range_dps": 90.0, "max_speed_dps": 150.0, "drop_rate": 0.10},
    {"id": "T-17", "name": "Gubitak paketa: 20%", "seconds": 26.0, "filter": "one_euro", "range_dps": 90.0, "max_speed_dps": 150.0, "drop_rate": 0.20},
    {"id": "T-18", "name": "Gubitak paketa: 30%", "seconds": 26.0, "filter": "one_euro", "range_dps": 90.0, "max_speed_dps": 150.0, "drop_rate": 0.30},
]


def run_test(tdef: dict, ip: str, out_telem_dir: Path, raw_dir: Path) -> bool:
    tid = tdef["id"]
    name = tdef["name"]
    raw_track = raw_dir / f"{tid}.track.csv"
    if not raw_track.exists():
        log.error("Nedostaje ulazna snimka: %s", raw_track)
        return False

    out_csv = out_telem_dir / f"{tid}.csv"
    out_track = out_telem_dir / f"{tid}.track.csv"

    log.info("=================================================================")
    log.info("POKUS %s: %s (%s s)", tid, name, tdef["seconds"])
    log.info("=================================================================")

    # 1. Reset to home reference pose
    try:
        from src.tools.home_pose import move_to_home
        log.info("-> Vraćam robota u referentnu pozu...")
        move_to_home(ip, speed=0.5)
        time.sleep(0.5)
    except Exception as exc:
        log.error("Neuspjelo vraćanje u home: %s", exc)
        return False

    # 2. Build CLI arguments
    cmd = [
        sys.executable, "-m", "src.pipeline.main",
        "--replay-track", str(raw_track),
        "--mode", "multi_joint",
        "--sink", "ursim",
        "--ip", ip,
        "--seconds", str(tdef["seconds"]),
        "--latency-csv", str(out_csv),
        "--track-csv", str(out_track),
        "--log-actual",
    ]
    if "filter" in tdef:
        cmd.extend(["--filter", tdef["filter"]])
    if "range_dps" in tdef:
        cmd.extend(["--range-dps", str(tdef["range_dps"])])
    if "max_speed_dps" in tdef:
        cmd.extend(["--max-speed-dps", str(tdef["max_speed_dps"])])
    if "estop_after" in tdef:
        cmd.extend(["--estop-after", str(tdef["estop_after"])])
    if "added_latency_ms" in tdef:
        cmd.extend(["--added-latency-ms", str(tdef["added_latency_ms"])])
    if "signal_timeout_s" in tdef:
        cmd.extend(["--signal-timeout-s", str(tdef["signal_timeout_s"])])
    if "drop_rate" in tdef:
        cmd.extend(["--drop-rate", str(tdef["drop_rate"])])

    # 3. Execute pipeline run
    res = subprocess.run(cmd, cwd=REPO_ROOT, check=False)
    if res.returncode != 0:
        log.error("Pipeline je vratio grešku %d za pokus %s", res.returncode, tid)
        return False

    # 4. Run track_analysis to produce summary JSON and figure
    if out_track.exists():
        from src.tools import track_analysis
        try:
            log.info("-> Analiza vjernosti praćenja za %s...", tid)
            track_analysis.main([str(out_track)])
        except Exception as exc:
            log.warning("Analiza nije uspjela za %s: %s", tid, exc)

    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Batch replay of lab tests on URSim")
    ap.add_argument("--ip", default="192.168.208.128", help="IP simulatora URSim")
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Direktorij za rezultate")
    ap.add_argument("--raw-dir", default=str(RAW_DIR), help="Direktorij sa sirovim podacima")
    ap.add_argument("--tests", default=None, help="Zarezom odvojeni ID-ovi (npr. T-02,T-03)")
    ap.add_argument("--skip-done", action="store_true", help="Preskoči već izvedene pokuse")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    out_dir = Path(args.out_dir)
    telem_dir = out_dir / "telemetry"
    telem_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = Path(args.raw_dir)

    target_ids = [s.strip() for s in args.tests.split(",")] if args.tests else None

    tests_to_run = [
        t for t in TEST_DEFINITIONS
        if target_ids is None or t["id"] in target_ids
    ]

    log.info("Započinjem batch replay %d pokusa na URSim (%s)...", len(tests_to_run), args.ip)
    t0 = time.time()
    success_count = 0

    for idx, tdef in enumerate(tests_to_run, 1):
        tid = tdef["id"]
        out_track = telem_dir / f"{tid}.track.csv"
        if args.skip_done and out_track.exists():
            log.info("[%d/%d] Pokus %s je već izveden — preskačem.", idx, len(tests_to_run), tid)
            success_count += 1
            continue

        log.info("[%d/%d] Pokrećem %s...", idx, len(tests_to_run), tid)
        ok = run_test(tdef, args.ip, telem_dir, raw_dir)
        if ok:
            success_count += 1

    # Return to home pose at the end
    try:
        from src.tools.home_pose import move_to_home
        move_to_home(args.ip, speed=0.5)
    except Exception:
        pass

    dt_total = time.time() - t0
    log.info("Batch replay dovršen: %d/%d uspješno u %.1f s (%.1f min).",
             success_count, len(tests_to_run), dt_total, dt_total / 60.0)

    # Run comparative analysis
    try:
        from src.tools.compare_live_vs_sim import generate_comparison
        generate_comparison(raw_dir, telem_dir, out_dir)
    except Exception as exc:
        log.warning("Generiranje usporedbe nije uspjelo: %s", exc)

    return 0 if success_count == len(tests_to_run) else 1


if __name__ == "__main__":
    raise SystemExit(main())
