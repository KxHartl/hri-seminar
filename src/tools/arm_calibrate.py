"""Guided 6-DOF axis calibration: measure ``arm_axes`` and write it to the config.

Which Euler component of which relative rotation *is* "shoulder pitch" depends on
how the rigid bodies' local axes came out in Motive, so it cannot be hard-coded —
and it changes whenever the bodies are rebuilt (2026-08-31: stream IDs changed,
which is exactly that). ``arm_inspect.py`` shows the raw components and leaves the
reading to you; this tool does the same measurement but decides and writes.

For each of six isolated motions it records a few seconds, decomposes the relevant
relative rotation, and picks the component with the largest excursion. The sign is
taken so that the instructed direction produces a POSITIVE channel. It also reports
the runner-up component, which is how you see whether a channel is cleanly separated
or coupled.

The operator is told what to do one line per second, with a countdown, exactly like
``joint_walkthrough``. The robot is not involved — nothing moves.

Usage:
    python -m src.tools.arm_calibrate                     # write to default.yaml
    python -m src.tools.arm_calibrate --seconds 8         # longer per motion
    python -m src.tools.arm_calibrate --dry-run           # measure, print, don't write
"""

from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
import time
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

from src.kinematics.arm_pose import RigidPose
from src.optitrack.sdk_natnet import DEFAULT_IDS, SDKRigidBodyReader

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG = REPO_ROOT / "src/config/default.yaml"

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

SHOULDER_SEQ = "ZXY"
WRIST_SEQ = "XYZ"
FOREARM_SEQ = "XYZ"

# key -> (instruction, which relative rotation, Euler sequence)
MOTIONS = [
    ("shoulder_pitch", "Podigni cijelu ISPRUŽENU ruku prema gore i vrati je dolje.",
     "shoulder", SHOULDER_SEQ),
    ("shoulder_yaw", "Pomakni ISPRUŽENU ruku u stranu (od tijela) i vrati je.",
     "shoulder", SHOULDER_SEQ),
    ("elbow", "Savij LAKAT do ~90° i ispruži natrag.", "forearm", FOREARM_SEQ),
    ("wrist_flex", "Savij ŠAKU prema gore/dolje (podlaktica miruje).", "wrist", WRIST_SEQ),
    ("wrist_dev", "Otkloni ŠAKU lijevo/desno (podlaktica miruje).", "wrist", WRIST_SEQ),
    ("wrist_axial", "Okreni PODLAKTICU (dlan gore -> dlan dolje) i natrag.",
     "forearm", FOREARM_SEQ),
]

STEP_PAUSE_S = 1.0


def say(msg: str = "", pause: float = STEP_PAUSE_S) -> None:
    print(msg, flush=True)
    time.sleep(pause)


def mean_rotation(rots: list[Rotation]) -> Rotation:
    """Average orientation (quaternion eigenvector method) — home must be steady."""
    q = np.array([r.as_quat() for r in rots])
    q *= np.sign(q[:, 3:4] + 1e-12)          # hemisphere-align before averaging
    _, vecs = np.linalg.eigh(q.T @ q)
    return Rotation.from_quat(vecs[:, -1])


class Recorder:
    """Pulls complete (all three bodies) frames from the live SDK stream."""

    def __init__(self, server: str, client: str, ids: dict[str, int]) -> None:
        self.ids = ids
        self.reader = SDKRigidBodyReader(server, client, use_multicast=False)
        self._it = self.reader._frames()

    def grab(self, seconds: float) -> list[tuple[RigidPose, RigidPose, RigidPose]]:
        u, f, h = self.ids["upper"], self.ids["fore"], self.ids["hand"]
        out: list[tuple[RigidPose, RigidPose, RigidPose]] = []
        t0 = time.time()
        while time.time() - t0 < seconds:
            poses = next(self._it)
            if not all(i in poses for i in (u, f, h)):
                continue
            out.append((RigidPose(*poses[u]), RigidPose(*poses[f]), RigidPose(*poses[h])))
        return out

    def close(self) -> None:
        self.reader.close()


def relative(kind: str, up: RigidPose, fo: RigidPose, ha: RigidPose,
             home: dict) -> Rotation:
    """Rotation whose Euler components a channel is decomposed from."""
    if kind == "shoulder":                       # upper arm vs world home
        return home["U"].inv() * up.rot()
    if kind == "forearm":                        # forearm vs upper arm, home-referenced
        return (home["U"].inv() * home["F"]).inv() * (up.rot().inv() * fo.rot())
    return (home["F"].inv() * home["H"]).inv() * (fo.rot().inv() * ha.rot())  # wrist


def measure(frames, kind: str, seq: str, home: dict) -> dict:
    e = np.array([relative(kind, u, f, h, home).as_euler(seq, degrees=True)
                  for u, f, h in frames])
    ptp = e.max(axis=0) - e.min(axis=0)
    idx = int(np.argmax(ptp))
    peak = e[np.argmax(np.abs(e[:, idx])), idx]
    runner = int(np.argsort(ptp)[-2])
    return {
        "seq": seq, "idx": idx, "sign": 1 if peak > 0 else -1,
        "ptp": float(ptp[idx]), "axis": seq[idx],
        "runner_axis": seq[runner], "runner_ptp": float(ptp[runner]),
        "n": len(frames),
    }


def render_axes(res: dict[str, dict], stamp: str) -> str:
    sh_yaw, sh_pitch = res["shoulder_yaw"], res["shoulder_pitch"]
    el, wf, wd, wa = res["elbow"], res["wrist_flex"], res["wrist_dev"], res["wrist_axial"]
    return (
        f"arm_axes:                                   # KALIBRIRANO {stamp} (arm_calibrate)\n"
        f"  shoulder: {{ seq: {SHOULDER_SEQ}, yaw_idx: {sh_yaw['idx']}, yaw_sign: {sh_yaw['sign']}, "
        f"pitch_idx: {sh_pitch['idx']}, pitch_sign: {sh_pitch['sign']} }}\n"
        f"  elbow:    {{ mode: orientation, seq: {FOREARM_SEQ}, idx: {el['idx']}, sign: {el['sign']} }}\n"
        f"  wrist:    {{ seq: {WRIST_SEQ}, flex_idx: {wf['idx']}, dev_idx: {wd['idx']}, "
        f"axial_idx: {wa['idx']}, signs: [{wf['sign']}, {wd['sign']}, {wa['sign']}],\n"
        f"              axial_from_forearm: true, forearm_seq: {FOREARM_SEQ}, "
        f"forearm_axial_idx: {wa['idx']}, forearm_axial_sign: {wa['sign']} }}\n"
    )


def write_axes(block: str, path: Path = CONFIG) -> None:
    """Replace the whole ``arm_axes:`` block, leaving the rest of the file alone."""
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r"^arm_axes:.*?(?=^[A-Za-z_]+:)", re.MULTILINE | re.DOTALL)
    if not pattern.search(text):
        raise SystemExit("Ne nalazim 'arm_axes:' blok u configu.")
    path.write_text(pattern.sub(block + "\n", text, count=1), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--server-ip", default="192.168.40.31")
    ap.add_argument("--client-ip", default="192.168.40.30")
    ap.add_argument("--seconds", type=float, default=6.0, help="snimanje po pokretu")
    ap.add_argument("--home-seconds", type=float, default=2.0, help="mirovanje za home")
    ap.add_argument("--id-upper", type=int, default=DEFAULT_IDS["upper"])
    ap.add_argument("--id-fore", type=int, default=DEFAULT_IDS["fore"])
    ap.add_argument("--id-hand", type=int, default=DEFAULT_IDS["hand"])
    ap.add_argument("--dry-run", action="store_true", help="ne piši u config")
    args = ap.parse_args(argv)

    ids = {"upper": args.id_upper, "fore": args.id_fore, "hand": args.id_hand}
    rec = Recorder(args.server_ip, args.client_ip, ids)

    print("=" * 78)
    print("KALIBRACIJA OSI RUKE (arm_axes) — robot se NE giba")
    print(f"Motive={args.server_ip}  ID-evi={ids}  {args.seconds:.0f} s po pokretu")
    print("=" * 78)
    say()
    say("Šest izoliranih pokreta. Svaki KREĆE i ZAVRŠAVA u ispruženoj ruci.")
    say("Radi samo traženi pokret — ostatak ruke miruje.")
    say()

    try:
        say("HOME: stani mirno s ISPRUŽENOM rukom ...")
        for c in (3, 2, 1):
            say(f"  {c} ...")
        home_frames = rec.grab(args.home_seconds)
        if len(home_frames) < 10:
            raise SystemExit("Premalo valjanih okvira — tijela se ne prate (vidi 00_provjera).")
        home = {
            "U": mean_rotation([u.rot() for u, _, _ in home_frames]),
            "F": mean_rotation([f.rot() for _, f, _ in home_frames]),
            "H": mean_rotation([h.rot() for _, _, h in home_frames]),
        }
        say(f"  home postavljen ({len(home_frames)} okvira).")
        say()

        res: dict[str, dict] = {}
        for k, (key, instruction, kind, seq) in enumerate(MOTIONS, start=1):
            print("-" * 78)
            say(f"POKRET {k}/{len(MOTIONS)} — {key}")
            say(f"  {instruction}")
            say(f"  Traje {args.seconds:.0f} s; kreni iz ispružene ruke.")
            for c in (3, 2, 1):
                say(f"  {c} ...")
            frames = rec.grab(args.seconds)
            if len(frames) < 20:
                raise SystemExit(f"Premalo okvira za '{key}' — provjeri praćenje.")
            m = measure(frames, kind, seq, home)
            res[key] = m
            sep = m["ptp"] / max(m["runner_ptp"], 1e-6)
            print(f"  -> os {m['axis']} (idx {m['idx']}), raspon {m['ptp']:.1f}°, "
                  f"predznak {m['sign']:+d}   [drugi po veličini: {m['runner_axis']} "
                  f"{m['runner_ptp']:.1f}°, odvojenost {sep:.1f}x]")
            if sep < 1.5:
                print("     ⚠ slaba odvojenost — pokret nije bio izoliran ili su osi spregnute.")
            say()
    finally:
        rec.close()

    stamp = _dt.date.today().isoformat()
    block = render_axes(res, stamp)
    print("-" * 78)
    print(block)
    if args.dry_run:
        print("--dry-run: config nije mijenjan.")
        return 0
    write_axes(block)
    print(f"Upisano u {CONFIG.relative_to(REPO_ROOT)}.")
    print("Sljedeće: .\\02_slobodno_gibanje.ps1 (svi zglobovi) — provjeri smjerove;")
    print("krivi smjer zgloba se popravlja u arm_mapping (invert: true) za taj zglob.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nPrekinuto (Ctrl-C) — config nije mijenjan.")
        raise SystemExit(130) from None
