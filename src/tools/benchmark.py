"""Stage 4 offline benchmarks on the real recordings.

Produces report-ready numbers and a figure:
  * flexion-angle filter comparison (jitter reduction vs lag) for each take,
  * sensitivity of the flexion angle to marker measurement noise,
  * a raw-vs-filtered comparison plot.

Results are persisted to ``data/processed/benchmarks_02092026/filter_bench.summary.json`` so the
numbers quoted in the report have a provenance file, not just stdout.

The filter comparison can run on either source:

  * the recorded exercise takes (marker positions -> hand flexion), or
  * ``--track`` : the angle actually logged during a live run
    (:mod:`src.pipeline.tracklog`), which is the real experimental signal --
    the elbow angle driving the robot -- rather than an old hand recording.

Sensitivity to marker noise needs raw marker positions, so it always runs on
the takes.

Usage:
    python -m src.tools.benchmark
    python -m src.tools.benchmark --track data/raw/lab_session_01092026_020000/telemetry/T-02.track.csv --joint 3
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.filtering.analysis import compare
from src.filtering.causal import ButterworthLowPass
from src.filtering.one_euro import OneEuroFilter
from src.kinematics.joint_angle import flexion_series, sensitivity
from src.optitrack.csv_loader import load_take

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT = REPO_ROOT / "data" / "processed"
TAKES = [
    REPO_ROOT / "data/raw/reference_mocap/vjezbe_02/hri_snimanje_vjezbe_02_x.csv",
    REPO_ROOT / "data/raw/reference_mocap/vjezbe_02/hri_snimanje_vjezbe_02_y.csv",
    REPO_ROOT / "data/raw/reference_mocap/vjezbe_02/hri_snimanje_vjezbe_02_z.csv",
]


def _angle_from_track(path: Path, joint: int | None) -> tuple[np.ndarray, float, str]:
    """Load the logged human input angle [rad] from a track CSV."""
    with path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise SystemExit(f"Prazan track CSV: {path}")
    cands = [k for k in rows[0] if k.startswith("in_J") and k.endswith("_deg")]
    if not cands:
        raise SystemExit(f"Nema 'in_J*_deg' kolona u {path}")
    col = f"in_J{joint}_deg" if joint is not None else cands[0]
    if col not in rows[0]:
        raise SystemExit(f"Nema kolone {col}; dostupno: {cands}")
    deg = np.array([float(r[col]) for r in rows])
    t = np.array([float(r["t_s"]) for r in rows])
    dt = float(np.median(np.diff(t))) if len(t) > 1 else 1 / 120.0
    fs = 1.0 / dt if dt > 0 else 120.0
    return np.radians(deg), fs, f"{path.name}:{col}"


def _report_filters(angle: np.ndarray, fs: float) -> list[dict]:
    print(f"  {'filtar':<22}{'jitter↓ [%]':>14}{'lag [ms]':>12}{'RMS vs raw [°]':>16}")
    out = []
    for m in compare(angle, fs):
        print(f"  {m.name:<22}{m.jitter_reduction_pct:>14.1f}"
              f"{m.lag_ms:>12.1f}{m.rms_vs_raw_deg:>16.3f}")
        out.append({"filter": m.name,
                    "jitter_reduction_pct": round(m.jitter_reduction_pct, 2),
                    "lag_ms": round(m.lag_ms, 2),
                    "rms_vs_raw_deg": round(m.rms_vs_raw_deg, 4)})
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Benchmark filtara i osjetljivosti")
    ap.add_argument("--track", default=None,
                    help="track CSV iz živog runa; filtri se mjere na STVARNOM signalu "
                         "(npr. data/raw/lab_session_01092026_020000/telemetry/T-02.track.csv)")
    ap.add_argument("--joint", type=int, default=None,
                    help="1-bazirani zglob u track CSV-u (npr. 3 za lakat/J3)")
    args = ap.parse_args(argv)

    OUT.mkdir(parents=True, exist_ok=True)
    results: dict = {"takes": [], "sensitivity": [], "track": None}
    print("=" * 78)
    print("Benchmark filtara i osjetljivosti")
    print("=" * 78)

    if args.track:
        angle, fs, label = _angle_from_track(Path(args.track), args.joint)
        rng = float(np.degrees(angle.max() - angle.min()))
        print()
        print(f"## ŽIVI SIGNAL — {label}  ({len(angle)} uzoraka @ {fs:.1f} Hz, "
              f"raspon ~{rng:.1f}°)")
        results["track"] = {"source": label, "n": int(len(angle)),
                            "fs_hz": round(fs, 1), "range_deg": round(rng, 1),
                            "filters": _report_filters(angle, fs)}

    for take_path in TAKES:
        take = load_take(take_path)
        fs = take.frame_rate_hz
        angle, ok = flexion_series(
            take.markers["zapesce"], take.markers["srednji"], take.markers["mali"])
        rng_deg = np.degrees(angle.max() - angle.min())
        print()
        print(f"## {take.take_name}  ({take.n_frames} okvira @ {fs:.0f} Hz, "
              f"raspon fleksije ~{rng_deg:.1f}°, valjanih frameova {100*ok.mean():.1f}%)")
        entry = {"take": take.take_name, "n_frames": int(take.n_frames),
                 "fs_hz": round(float(fs), 1), "range_deg": round(float(rng_deg), 1),
                 "filters": _report_filters(angle, fs)}
        results["takes"].append(entry)

        print("  osjetljivost na šum markera (RMS odstupanje kuta):")
        for noise in (0.5, 1.0, 2.0):
            sv = sensitivity(take.markers["zapesce"], take.markers["srednji"],
                             take.markers["mali"], noise_mm=noise)
            print(f"    šum {noise:>3.1f} mm -> RMS {sv['rms_deg']:.3f}°, "
                  f"max {sv['max_deg']:.3f}°")
            results["sensitivity"].append(
                {"take": take.take_name, "noise_mm": noise,
                 "rms_deg": round(float(sv["rms_deg"]), 4),
                 "max_deg": round(float(sv["max_deg"]), 4)})

    # Comparison plot on the first take.
    take = load_take(TAKES[0])
    angle, _ = flexion_series(
        take.markers["zapesce"], take.markers["srednji"], take.markers["mali"])
    deg = np.degrees(angle)
    t = np.arange(len(deg)) / take.frame_rate_hz
    oe = OneEuroFilter(freq_hz=take.frame_rate_hz, min_cutoff=1.0, beta=0.007)
    bw = ButterworthLowPass(fs_hz=take.frame_rate_hz, cutoff_hz=6.0, order=2)
    oe_out = np.array([oe(x, ti) for x, ti in zip(deg, t)])
    bw_out = np.array([bw(x) for x in deg])

    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(t, deg, color="0.7", lw=0.8, label="sirovo")
    ax.plot(t, oe_out, "b-", lw=1.4, label="One-Euro")
    ax.plot(t, bw_out, "r-", lw=1.2, label="Butterworth 6 Hz")
    ax.set_xlabel("vrijeme [s]"); ax.set_ylabel("kut fleksije [°]")
    ax.set_title(f"Filtriranje kuta fleksije — {take.take_name}")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout()
    out_png = OUT / "filter_comparison.png"
    fig.savefig(out_png, dpi=130)

    out_json = OUT / "filter_bench.summary.json"
    out_json.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print()
    print(f"Graf spremljen  -> {out_png}")
    print(f"Summary spremljen -> {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
