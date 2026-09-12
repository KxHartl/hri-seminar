"""Guided joint-by-joint control test on the real robot, one joint per step.

The live 1-DOF bridge (``live_sender --sdk``) streams the operator's ELBOW angle;
this walks that one signal across the robot joints, one at a time, so every joint
is verified separately: does it move, in the expected direction, within its band,
and how closely does the robot follow the command. Between steps the robot is
returned to the reference pose (``robot.home_q_deg``) so each joint starts from
the same place and nothing drifts across steps.

Every instruction is printed one second apart, so the operator can read and react
before anything moves, and each step ends with the measured numbers for that joint.

Prerequisite: the bridge is already streaming on ``--port`` (the run_scripts
wrappers start it for you).

Usage:
    python -m src.tools.joint_walkthrough --ip 192.168.40.50
    python -m src.tools.joint_walkthrough --ip 192.168.40.50 --joints 2,3 --seconds 10
    python -m src.tools.joint_walkthrough --ip 192.168.40.50 --sink dry_run   # proba
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

# 0-based joint index -> (pendant label, name, range [deg], max speed [deg/s], what to watch)
JOINTS = {
    0: ("J1", "baza", 15, 12, "cijela ruka se zakreće oko baze — najviše prostora treba ovdje"),
    1: ("J2", "rame", 12, 10, "ruka se diže/spušta; pazi na stol i kabele"),
    2: ("J3", "lakat", 25, 20, "glavni kanal rada (lakat -> lakat)"),
    3: ("J4", "zapešće 1", 25, 20, "mali pokret na vrhu ruke"),
    4: ("J5", "zapešće 2", 25, 20, "mali pokret na vrhu ruke"),
    5: ("J6", "zapešće 3", 30, 25, "rotacija alata, najmanji rizik"),
}

STEP_PAUSE_S = 1.0


def say(msg: str = "", pause: float = STEP_PAUSE_S) -> None:
    print(msg, flush=True)
    time.sleep(pause)


def go_home(ip: str, speed: float) -> None:
    cmd = [sys.executable, "-m", "src.tools.home_pose", "--ip", ip, "--speed", str(speed), "--yes"]
    subprocess.run(cmd, cwd=REPO_ROOT, check=False)


def run_joint(args, idx: int, out_dir: Path) -> Path | None:
    label, name, rng, spd, watch = JOINTS[idx]
    rng = args.range_dps or rng
    spd = args.max_speed_dps or spd
    track = out_dir / f"{label}.track.csv"
    cmd = [
        sys.executable, "-m", "src.pipeline.main",
        "--external", "--port", str(args.port),
        "--sink", args.sink, "--ip", args.ip,
        "--joint", str(idx),
        "--seconds", str(args.seconds),
        "--range-dps", str(rng), "--max-speed-dps", str(spd),
        "--latency-csv", str(out_dir / f"{label}.csv"),
        "--track-csv", str(track), "--log-actual",
    ]
    res = subprocess.run(cmd, cwd=REPO_ROOT, check=False)
    if res.returncode != 0:
        print(f"  !! pipeline je vratio kod {res.returncode} — preskačem analizu.")
        return None
    return track


def report(track: Path) -> None:
    from src.tools.track_analysis import analyse
    try:
        res = analyse(track)
    except Exception as exc:  # noqa: BLE001 - a failed analysis must not stop the walk
        print(f"  !! analiza nije uspjela: {exc}")
        return
    for jname, j in res["joints"].items():
        i2c, c2a = j["input_to_command"], j["command_to_actual"]
        lo, hi = j["range_in_deg"]
        clo, chi = j["range_cmd_deg"]
        saf = j.get("safety_events", {})
        print(f"  {jname}: ulaz {lo:+.1f}..{hi:+.1f}°   naredba {clo:+.1f}..{chi:+.1f}°")
        print(f"       naredba->stvarno RMSE {c2a['rmse_deg']:.2f}°  lag {c2a['lag_ms']:.0f} ms"
              f"  (r={c2a['corr']:.3f})")
        print(f"       ulaz->naredba    RMSE {i2c['rmse_deg']:.2f}°  lag {i2c['lag_ms']:.0f} ms")
        if saf:
            print("       clamp: " + ", ".join(f"{k}={v}" for k, v in saf.items()))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ip", required=True, help="IP robota")
    ap.add_argument("--port", type=int, default=51000, help="UDP port mosta")
    ap.add_argument("--sink", default="ur3e", help="ur3e | ursim | dry_run (proba bez gibanja)")
    ap.add_argument("--joints", default="0,1,2,3,4,5", help="koje zglobove testirati (0-based)")
    ap.add_argument("--seconds", type=float, default=12.0, help="trajanje po zglobu")
    ap.add_argument("--range-dps", type=float, default=None, help="override raspona za SVE zglobove")
    ap.add_argument("--max-speed-dps", type=float, default=None, help="override brzine za SVE")
    ap.add_argument("--home-speed", type=float, default=0.3, help="moveJ brzina [rad/s]")
    ap.add_argument("--no-home", action="store_true", help="ne vraćaj u referentnu pozu")
    args = ap.parse_args(argv)

    idxs = [int(x) for x in args.joints.split(",") if x.strip() != ""]
    bad = [i for i in idxs if i not in JOINTS]
    if bad:
        raise SystemExit(f"Nepoznati zglobovi: {bad} (dopušteno 0..5)")

    out_dir = REPO_ROOT / "data/raw/lab_session_01092026_020000/telemetry/exploratory/walkthrough"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 78)
    print("HOD PO ZGLOBOVIMA — kut lakta vozi jedan po jedan zglob robota")
    print(f"robot={args.ip}  sink={args.sink}  {args.seconds:.0f} s po zglobu  "
          f"zglobovi={[JOINTS[i][0] for i in idxs]}")
    print("=" * 78)
    say()
    say("SIGURNOST: nitko u radnom prostoru robota, e-stop u ruci.")
    say("Osoba s markerima stoji izvan dosega robota i miče SAMO lakat.")
    say("Prekid u bilo kojem trenutku: Ctrl-C (robot stane, servoStop).")
    say()

    for k, idx in enumerate(idxs, start=1):
        label, name, rng, spd, watch = JOINTS[idx]
        rng = args.range_dps or rng
        spd = args.max_speed_dps or spd
        print("-" * 78)
        say(f"KORAK {k}/{len(idxs)} — {label} ({name})")
        say(f"  granice: ±{rng:.0f}°, najviše {spd:.0f}°/s")
        say(f"  pazi: {watch}")
        if not args.no_home and args.sink != "dry_run":
            say("  vraćam robota u referentnu pozu (ravna ispružena ruka) ...")
            go_home(args.ip, args.home_speed)
        say(f"  ZADATAK: savijaj i ispružaj LAKAT, sporo i ravnomjerno, {args.seconds:.0f} s.")
        say(f"  GLEDAJ: miče li se {label} ({name}) i u kojem smjeru.")
        for c in (3, 2, 1):
            say(f"  kreće za {c} ...")
        run = run_joint(args, idx, out_dir)
        print()
        if run is not None:
            report(run)
        say()

    print("-" * 78)
    if not args.no_home and args.sink != "dry_run":
        say("Vraćam robota u referentnu pozu na kraju ...")
        go_home(args.ip, args.home_speed)
    print(f"Gotovo. CSV-ovi i figure: {out_dir.relative_to(REPO_ROOT)}")
    print("Za detaljnu analizu: python -m src.tools.track_analysis "
          f"{out_dir.relative_to(REPO_ROOT)}/J3.track.csv")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nPrekinuto (Ctrl-C).")
        raise SystemExit(130) from None
