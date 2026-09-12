"""Reference pose ("home") management for the real robot.

The reference pose is NOT the robot's own home: it is the joint vector that
corresponds to the operator standing with a **straight, extended arm** — the
pose every run must start from so that the mapper's home frame and the robot's
starting ``q`` mean the same thing in every run. Without it each run re-homes
wherever the previous run left the arm, and the joint band drifts (observed
2026-08-31: elbow 0 deg -> 20 deg -> 37 deg over three runs).

It lives in ``src/config/default.yaml`` as ``robot.home_q_deg``.

Usage:
    python -m src.tools.home_pose --ip 192.168.40.50            # show + move there
    python -m src.tools.home_pose --ip 192.168.40.50 --show     # no motion
    python -m src.tools.home_pose --ip 192.168.40.50 --capture  # store current pose
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG = REPO_ROOT / "src/config/default.yaml"

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass


def read_home_deg(path: Path = CONFIG) -> list[float] | None:
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    v = (cfg.get("robot") or {}).get("home_q_deg")
    return [float(x) for x in v] if v else None


def write_home_deg(values: list[float], path: Path = CONFIG) -> None:
    """Rewrite just the ``home_q_deg`` line, leaving comments/format untouched."""
    text = path.read_text(encoding="utf-8")
    rendered = "[" + ", ".join(f"{v:g}" for v in values) + "]"
    new_line = f"  home_q_deg: {rendered}"
    pattern = re.compile(r"^  home_q_deg:.*$", re.MULTILINE)
    if not pattern.search(text):
        raise SystemExit("Ne nalazim 'home_q_deg' u configu — dodaj ga ručno.")
    keep_comment = re.search(r"^  home_q_deg:[^#]*(#.*)$", text, re.MULTILINE)
    if keep_comment:
        new_line = f"{new_line}   {keep_comment.group(1)}"
    path.write_text(pattern.sub(new_line, text, count=1), encoding="utf-8")


def _fmt(q_rad) -> str:
    return "[" + ", ".join(f"{math.degrees(v):7.2f}" for v in q_rad) + "] deg"


def move_to_home(ip: str, speed: float = 0.5) -> None:
    """Move robot to configured home_q_deg via RTDE."""
    home_deg = read_home_deg()
    if home_deg is None:
        raise ValueError("robot.home_q_deg not found in config.")
    home_rad = [math.radians(v) for v in home_deg]
    from src.robot.rtde_backend import RTDEBackend
    sink = RTDEBackend(ip, variant="ur3e")
    sink.connect()
    try:
        sink.move_j(home_rad, speed=speed)
    finally:
        sink.disconnect()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ip", required=True, help="IP robota (npr. 192.168.40.50)")
    ap.add_argument("--show", action="store_true", help="samo ispiši, ne miči robota")
    ap.add_argument("--capture", action="store_true",
                    help="spremi TRENUTNU pozu robota kao referentnu (piše u config)")
    ap.add_argument("--speed", type=float, default=0.3, help="moveJ brzina [rad/s]")
    ap.add_argument("--yes", action="store_true", help="bez pitanja (za skripte)")
    args = ap.parse_args()

    import rtde_receive
    rr = rtde_receive.RTDEReceiveInterface(args.ip)
    actual = list(rr.getActualQ())
    print(f"Trenutna poza : {_fmt(actual)}")

    if args.capture:
        deg = [round(math.degrees(v), 2) for v in actual]
        write_home_deg(deg)
        print(f"Spremljeno kao referentna poza -> {deg}")
        print(f"  ({CONFIG.relative_to(REPO_ROOT)}, ključ robot.home_q_deg)")
        return 0

    home_deg = read_home_deg()
    if home_deg is None:
        print("U configu nema robot.home_q_deg — snimi je s --capture.")
        return 1
    home_rad = [math.radians(v) for v in home_deg]
    print(f"Referentna poza: {_fmt(home_rad)}")
    delta = [abs(math.degrees(a - b)) for a, b in zip(actual, home_rad)]
    print(f"Odstupanje     : {[round(d, 2) for d in delta]} deg  (max {max(delta):.2f})")

    if args.show:
        return 0
    if max(delta) < 0.5:
        print("Robot je već u referentnoj pozi — ne mičem ga.")
        return 0
    if not args.yes:
        ans = input("Pomaknuti robota u referentnu pozu? Prostor mora biti prazan [da/ne]: ")
        if ans.strip().lower() not in ("da", "d", "yes", "y"):
            print("Odustajem.")
            return 1

    from src.robot.rtde_backend import RTDEBackend
    sink = RTDEBackend(args.ip, variant="ur3e")
    sink.connect()
    try:
        print(f"moveJ -> referentna poza (brzina {args.speed} rad/s) ...")
        sink.move_j(home_rad, speed=args.speed)
    finally:
        sink.disconnect()
    print(f"Gotovo. Poza: {_fmt(rr.getActualQ())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
