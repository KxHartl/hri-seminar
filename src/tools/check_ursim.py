"""Verify RTDE connectivity to a UR controller (URSim or real UR3e).

Reads robot state via the RTDE receive interface, then (optionally) performs a
small, slow ``servoJ`` sweep on a single joint to confirm the control path works
end-to-end. Defaults are conservative and intended for the URSim simulator.

Usage:
    python -m src.tools.check_ursim --ip 192.168.208.128
    python -m src.tools.check_ursim --ip 192.168.208.128 --no-move   # state only
"""

from __future__ import annotations

import argparse
import math
import sys

# Windows konzola je često cp1252 → osiguraj UTF-8 ispis (ASCII se ionako koristi niže).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

DEFAULT_IP = "192.168.208.128"
JOINT_INDEX = 4            # wrist_2 / J5 (0-based)
SWEEP_AMP_DEG = 5.0        # peak amplitude of the test sweep [deg]
SWEEP_PERIOD_S = 4.0       # one full back-and-forth [s]
CONTROL_DT = 1.0 / 125.0   # servoJ control period [s]
SERVOJ_LOOKAHEAD = 0.1     # [s]
SERVOJ_GAIN = 300          # [-]
JOINT_NAMES = ("base", "shoulder", "elbow", "wrist_1", "wrist_2", "wrist_3")


def _fmt_deg(q_rad: list[float]) -> str:
    return "[" + ", ".join(f"{math.degrees(q):7.2f}" for q in q_rad) + "] deg"


def read_state(ip: str):
    """Connect the receive interface and print robot state. Returns actual q."""
    import rtde_receive

    print(f"→ Spajam RTDE receive na {ip} ...")
    rr = rtde_receive.RTDEReceiveInterface(ip)
    try:
        q = rr.getActualQ()
        print(f"  ✓ Povezano. Robot mode={rr.getRobotMode()} "
              f"safety mode={rr.getSafetyMode()}")
        print(f"  Trenutni zglobovi: {_fmt_deg(q)}")
        return q
    finally:
        rr.disconnect()


def sweep_joint(ip: str, q_home: list[float]) -> None:
    """Small sinusoidal servoJ sweep on JOINT_INDEX around the current pose."""
    import rtde_control

    print(f"→ Spajam RTDE control na {ip} ...")
    rc = rtde_control.RTDEControlInterface(ip)
    amp = math.radians(SWEEP_AMP_DEG)
    n_steps = int(SWEEP_PERIOD_S / CONTROL_DT)
    print(f"  ✓ Control spojen. Sweep J{JOINT_INDEX + 1} ({JOINT_NAMES[JOINT_INDEX]}) "
          f"±{SWEEP_AMP_DEG}° kroz {SWEEP_PERIOD_S}s ...")
    try:
        for i in range(n_steps + 1):
            t_start = rc.initPeriod()
            phase = 2.0 * math.pi * i / n_steps
            q = list(q_home)
            q[JOINT_INDEX] = q_home[JOINT_INDEX] + amp * math.sin(phase)
            rc.servoJ(q, 0.0, 0.0, CONTROL_DT, SERVOJ_LOOKAHEAD, SERVOJ_GAIN)
            rc.waitPeriod(t_start)
        rc.servoStop()
        print("  ✓ Sweep završen, servoStop OK.")
    finally:
        rc.stopScript()
        rc.disconnect()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RTDE connectivity check (URSim/UR3e)")
    parser.add_argument("--ip", default=DEFAULT_IP, help="UR controller IP")
    parser.add_argument("--no-move", action="store_true",
                        help="samo pročitaj stanje, bez gibanja")
    args = parser.parse_args(argv)

    try:
        q_home = read_state(args.ip)
    except Exception as exc:  # noqa: BLE001 - dijagnostika veze
        print(f"  ✗ Receive veza nije uspjela: {exc}", file=sys.stderr)
        return 1

    if args.no_move:
        print("Gotovo (state-only).")
        return 0

    try:
        sweep_joint(args.ip, q_home)
    except Exception as exc:  # noqa: BLE001
        print(f"  ✗ Control/servoJ nije uspio: {exc}", file=sys.stderr)
        print("    Provjeri: URSim u 'Remote Control' modu, robot uključen i "
              "brake released, program ne blokira RTDE.", file=sys.stderr)
        return 2

    print("Gotovo. RTDE control put potvrđen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
