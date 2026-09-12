"""Pre-lab readiness check — fail at home, not in the lab.

Verifies everything the session protocol (``testing/lab/protocols/08_session_plan.md``)
depends on: the venv actually has the robot/analysis packages, the NatNet SDK is
importable from wherever it lives on this machine (it is not vendored into the
repo, so a cleaned Downloads folder silently breaks the live source), the config
is present and calibrated, and the angle-logging path imports.

Optionally pings the lab hosts when run on site.

Usage:
    python -m src.tools.preflight
    python -m src.tools.preflight --robot 192.168.40.50 --motive 192.168.40.31
"""

from __future__ import annotations

import argparse
import importlib
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

OK, FAIL, WARN = "  OK  ", " FAIL ", " WARN "
_results: list[tuple[str, str, str]] = []


def check(name: str, status: str, detail: str = "") -> None:
    _results.append((status, name, detail))
    print(f"[{status}] {name}" + (f"  — {detail}" if detail else ""))


def _packages() -> None:
    for mod, why in [
        ("rtde_control", "upravljanje robotom"),
        ("rtde_receive", "čitanje stanja robota (--log-actual)"),
        ("numpy", "analiza"),
        ("scipy", "6-DOF rotacije + filtri"),
        ("yaml", "konfiguracija"),
        ("matplotlib", "figure"),
    ]:
        try:
            importlib.import_module(mod)
            check(f"paket {mod}", OK, why)
        except ImportError:
            check(f"paket {mod}", FAIL, f"nedostaje ({why}) — koristiš li .venv?")


def _natnet_sdk() -> None:
    from src.optitrack.sdk_natnet import DEFAULT_SDK

    path = os.environ.get("NATNET_SDK", DEFAULT_SDK)
    src = "env NATNET_SDK" if "NATNET_SDK" in os.environ else "ugrađeni default"
    if not Path(path).is_dir():
        check("NatNet SDK", FAIL, f"nema direktorija ({src}): {path}")
        return
    if path not in sys.path:
        sys.path.insert(0, path)
    try:
        importlib.import_module("NatNetClient")
        check("NatNet SDK", OK, f"{src}: {path}")
    except ImportError as exc:
        check("NatNet SDK", FAIL, f"nalazi se, ali se ne uvozi: {exc}")


def _config() -> None:
    from src.pipeline.main import load_config

    cfg_path = REPO_ROOT / "src/config/default.yaml"
    try:
        cfg = load_config(cfg_path)
    except Exception as exc:                       # noqa: BLE001 - report anything
        check("config", FAIL, f"{cfg_path}: {exc}")
        return
    check("config", OK, str(cfg_path.relative_to(REPO_ROOT)))

    axes = cfg.get("arm_axes", {})
    if axes.get("shoulder") and axes.get("elbow") and axes.get("wrist"):
        check("arm_axes (6-DOF kalibracija)", OK,
              "popunjeno — provjeri arm_inspect ako su rigid bodyji iznova napravljeni")
    else:
        check("arm_axes (6-DOF kalibracija)", FAIL, "nepotpuno — pokreni arm_inspect.py")

    n = len(cfg.get("arm_mapping", []))
    check("arm_mapping", OK if n == 6 else FAIL, f"{n} kanala (očekivano 6)")


def _logging_path() -> None:
    try:
        from src.pipeline.delay import DelayLine            # noqa: F401
        from src.pipeline.tracklog import TrackLog          # noqa: F401
        from src.robot.base import RobotSink
        assert hasattr(RobotSink, "get_actual_q")
        check("logiranje kutova (track/delay/actual)", OK, "spremno")
    except Exception as exc:                                # noqa: BLE001
        check("logiranje kutova", FAIL, str(exc))

    try:
        importlib.import_module("src.tools.track_analysis")
        check("alat track_analysis", OK, "spreman za provjeru runa na licu mjesta")
    except Exception as exc:                                # noqa: BLE001
        check("alat track_analysis", FAIL, str(exc))


def _lab_docs() -> None:
    for rel in ["testing/lab/protocols/08_session_plan.md", "testing/lab/protocols/cheatsheet.md",
                "testing/lab/templates/run_log.csv",
                "testing/lab/templates/safety_signoff.md"]:
        p = REPO_ROOT / rel
        check(f"dokument {rel}", OK if p.exists() else FAIL,
              "" if p.exists() else "nedostaje")
    results = REPO_ROOT / "data/raw/lab_session_01092026_020000/telemetry"
    media = results / "media"
    check("mapa za rezultate", OK if results.is_dir() else FAIL, str(results))
    check("mapa za medije", OK if media.is_dir() else WARN,
          "foto postava i videi sigurnosnih testova idu ovamo")


def _ping(host: str, label: str) -> None:
    flag = "-n" if sys.platform == "win32" else "-c"
    try:
        r = subprocess.run(["ping", flag, "1", "-w", "1500", host],
                           capture_output=True, timeout=10)
        check(f"{label} ({host})", OK if r.returncode == 0 else FAIL,
              "odgovara" if r.returncode == 0 else "ne odgovara")
    except Exception as exc:                                # noqa: BLE001
        check(f"{label} ({host})", FAIL, str(exc))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Provjera spremnosti prije labosa")
    ap.add_argument("--robot", default=None, help="IP robota (npr. 192.168.40.50)")
    ap.add_argument("--motive", default=None, help="IP Motive računala (npr. 192.168.40.31)")
    args = ap.parse_args(argv)

    print("=" * 78)
    print("PREFLIGHT — spremnost za lab sesiju")
    print(f"Python: {sys.version.split()[0]}  ({sys.executable})")
    print("=" * 78)

    _packages()
    _natnet_sdk()
    _config()
    _logging_path()
    _lab_docs()
    if args.robot:
        _ping(args.robot, "robot")
    if args.motive:
        _ping(args.motive, "Motive")

    fails = [r for r in _results if r[0] == FAIL]
    warns = [r for r in _results if r[0] == WARN]
    print("=" * 78)
    if fails:
        print(f"NIJE SPREMNO — {len(fails)} problema:")
        for _, name, detail in fails:
            print(f"  - {name}: {detail}")
        return 1
    print(f"SPREMNO ({len(_results)} provjera, {len(warns)} upozorenja).")
    print("Sljedeće: pytest src/tests -q, pa testing/lab/protocols/08_session_plan.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
