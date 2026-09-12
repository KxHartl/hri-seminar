"""Standalone OptiTrack replay -> UDP sender (separate process).

Running the sender in its own process mirrors the real topology (an external
OptiTrack/Motive box streaming UDP into our pipeline) and avoids CPython
GIL contention with the in-process control loop, so the replay holds its native
120 Hz. Point the pipeline's receiver at the same host/port.

Usage:
    python -m src.tools.replay_sender --port 51000 \
        --take data/raw/reference_mocap/vjezbe_02/hri_snimanje_vjezbe_02_x.csv
"""

from __future__ import annotations

import argparse
import ctypes
import logging
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

from src.optitrack.replay_source import ReplaySource, TrackReplaySource, send_over_udp

REPO_ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="OptiTrack replay -> UDP sender")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=51000)
    ap.add_argument("--take", default="data/raw/reference_mocap/vjezbe_02/hri_snimanje_vjezbe_02_x.csv")
    ap.add_argument("--track", default=None,
                    help="replay a 6-DOF .track.csv recording instead of a marker take")
    ap.add_argument("--markers", nargs="+", default=["zapesce", "palac", "srednji", "mali"])
    ap.add_argument("--loop", action="store_true", default=True)
    ap.add_argument("--drop-rate", type=float, default=0.0)
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
    if sys.platform == "win32":
        ctypes.windll.winmm.timeBeginPeriod(1)   # accurate sub-15 ms sleeps

    if args.track:
        track_path = REPO_ROOT / args.track
        source = TrackReplaySource(track_path, loop=args.loop)
        logging.info("Šaljem 6-DOF track %s -> %s:%d (drop=%.2f)",
                     track_path.name, args.host, args.port, args.drop_rate)
    else:
        take = REPO_ROOT / args.take
        source = ReplaySource(take, marker_names=tuple(args.markers), loop=args.loop)
        logging.info("Šaljem %s -> %s:%d (drop=%.2f)", take.name, args.host, args.port, args.drop_rate)
    try:
        send_over_udp(source, args.host, args.port, drop_rate=args.drop_rate)
    except KeyboardInterrupt:
        logging.info("Sender zaustavljen.")
    finally:
        if sys.platform == "win32":
            ctypes.windll.winmm.timeEndPeriod(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
