"""Bridge: live OptiTrack (Motive NatNet) -> our UDP marker protocol.

Runs in its own process so the NatNet client never contends with the pipeline's
control loop (GIL) and the pipeline stays unchanged (run it with ``--external``).
Identical pattern to ``replay_sender`` — only the marker source differs.

Usage:
    # Smoke-test the whole live path WITHOUT Motive (synthetic flexing hand):
    python -m src.tools.live_sender --mock --port 51000

    # Real Motive stream (fill in IPs; confirm NatNet/network details in the lab):
    python -m src.tools.live_sender --server-ip 192.168.x.x --client-ip 192.168.x.y \
        --port 51000 [--multicast]

    # Arm-segment elbow angle via the official SDK (rigid bodies by stream ID):
    python -m src.tools.live_sender --sdk --server-ip 192.168.x.x --client-ip 192.168.x.y \
        --id-upper 25 --id-fore 24 --id-hand 16 --port 51000

    # Full 6-DOF arm mimicry (3 rigid bodies -> 6 channels; pair with --mode multi_joint):
    python -m src.tools.live_sender --arm --server-ip 192.168.x.x --client-ip 192.168.x.y \
        --id-upper 25 --id-fore 24 --id-hand 16 --port 51000
"""

from __future__ import annotations

import argparse
import ctypes
import logging
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

from pathlib import Path

from src.optitrack.replay_source import send_over_udp

DEFAULT_MARKER_MAP = {
    "zapesce": "zapesce", "srednji": "srednji", "mali": "mali", "palac": "palac",
}
DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "src/config/default.yaml"


def _load_arm_axes(config_path: str | None) -> dict | None:
    """Load the ``arm_axes`` block from the pipeline config (calibration output)."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as fh:
            return yaml.safe_load(fh).get("arm_axes")
    except (OSError, KeyError, AttributeError) as exc:
        logging.warning("Ne mogu učitati arm_axes iz %s (%s); koristim defaulte.",
                        path, exc)
        return None


def _build_source(args):
    if args.mock_arm:
        from src.optitrack.mock_source import MockArmSource
        logging.info("MOCK ARM izvor (6 sintetičkih kanala) — bez Motivea. "
                     "Pipeline pokreni s --mode multi_joint.")
        return MockArmSource(rate_hz=args.rate)
    if args.mock:
        from src.optitrack.mock_source import MockMarkerSource
        logging.info("MOCK izvor (sintetička fleksija) — bez Motivea.")
        return MockMarkerSource(rate_hz=args.rate)
    if args.arm:
        from src.optitrack.sdk_arm_source import SDKArmSource
        ids = {"upper": args.id_upper, "fore": args.id_fore, "hand": args.id_hand}
        axes = _load_arm_axes(args.config)
        logging.info("SDK arm izvor (6-DOF mimikrija): server=%s client=%s ids=%s "
                     "multicast=%s axes=%s", args.server_ip, args.client_ip, ids,
                     args.multicast, axes)
        return SDKArmSource(
            server_ip=args.server_ip,
            client_ip=args.client_ip,
            ids=ids,
            use_multicast=args.multicast,
            sdk_path=args.sdk_path,
            axes=axes,
            median=args.median,
        )
    if args.sdk:
        from src.optitrack.sdk_segment_source import SDKSegmentSource
        ids = {"upper": args.id_upper, "fore": args.id_fore, "hand": args.id_hand}
        logging.info("SDK segment izvor (kut lakta): server=%s client=%s ids=%s "
                     "multicast=%s", args.server_ip, args.client_ip, ids, args.multicast)
        return SDKSegmentSource(
            server_ip=args.server_ip,
            client_ip=args.client_ip,
            ids=ids,
            use_multicast=args.multicast,
            sdk_path=args.sdk_path,
            median=args.median,
        )
    from src.optitrack.live_source import LiveNatNetSource
    logging.info("NatNet izvor: server=%s client=%s multicast=%s",
                 args.server_ip, args.client_ip, args.multicast)
    return LiveNatNetSource(
        server_ip=args.server_ip,
        client_ip=args.client_ip,
        use_multicast=args.multicast,
        marker_name_map=DEFAULT_MARKER_MAP,
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="OptiTrack NatNet -> UDP bridge")
    ap.add_argument("--host", default="127.0.0.1", help="pipeline (receiver) host")
    ap.add_argument("--port", type=int, default=51000)
    ap.add_argument("--mock", action="store_true", help="sintetički izvor bez Motivea (1-DOF)")
    ap.add_argument("--mock-arm", action="store_true",
                    help="sintetičkih 6 kanala bez Motivea (suha proba --mode multi_joint)")
    ap.add_argument("--rate", type=float, default=120.0, help="mock rate [Hz]")
    ap.add_argument("--server-ip", default="127.0.0.1", help="Motive server IP")
    ap.add_argument("--client-ip", default="127.0.0.1", help="lokalni NIC IP")
    ap.add_argument("--multicast", action="store_true", help="multicast umjesto unicast")
    ap.add_argument("--sdk", action="store_true",
                    help="rigid-body segment izvor preko službenog NatNet SDK-a (kut lakta)")
    ap.add_argument("--arm", action="store_true",
                    help="puna 6-DOF mimikrija ruke (3 rigid bodyja -> 6 kanala)")
    ap.add_argument("--config", default=None,
                    help="config za arm_axes (default: src/config/default.yaml)")
    ap.add_argument("--id-upper", type=int, default=25, help="stream ID nadlaktice")
    ap.add_argument("--id-fore", type=int, default=24, help="stream ID podlaktice")
    ap.add_argument("--id-hand", type=int, default=16, help="stream ID šake")
    ap.add_argument("--median", type=int, default=3,
                    help="medijan prozor protiv iglica u izvoru (1 = isključeno)")
    ap.add_argument("--sdk-path", default=None,
                    help="putanja do NatNetSDK PythonClient (inače env NATNET_SDK)")
    ap.add_argument("--drop-rate", type=float, default=0.0)
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
    if sys.platform == "win32":
        ctypes.windll.winmm.timeBeginPeriod(1)
    try:
        source = _build_source(args)
        logging.info("Šaljem markere -> %s:%d", args.host, args.port)
        send_over_udp(source, args.host, args.port, drop_rate=args.drop_rate)
    except KeyboardInterrupt:
        logging.info("Bridge zaustavljen.")
    finally:
        if sys.platform == "win32":
            ctypes.windll.winmm.timeEndPeriod(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
