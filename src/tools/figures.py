"""Report figures and tables from the recorded lab runs.

Reads the end-to-end latency CSVs and ``*.summary.json`` files under
``data/raw/lab_session_01092026_020000/telemetry/`` and renders publication-ready assets into the tracked
``docs/`` tree:

  * ``docs/figures/latency_hist.png``      -- end-to-end latency on the real UR3
    (median / p95 / p99 marked),
  * ``docs/figures/interarrival_hist.png`` -- frame inter-arrival = sampling-rate
    stability (120 Hz target),
  * ``docs/figures/step_response.png``     -- copied from data/processed (phase 5),
  * ``docs/figures/filter_comparison.png`` -- copied from data/processed (phase 3),
  * ``docs/tables/results.tex``            -- LaTeX table of the clean runs.

Latency/inter-arrival come from the real-robot run ``ur3-arm-6dof``. The two
copied PNGs are produced by ``src.tools.step_response`` and ``src.tools.benchmark``
(run those first). Idempotent; safe to re-run.

Usage:
    python -m src.tools.figures
"""

from __future__ import annotations

import csv
import json
import shutil
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS = REPO_ROOT / "data/raw/lab_session_01092026_020000/telemetry"
PROCESSED = REPO_ROOT / "data" / "processed"
FIGURES = REPO_ROOT / "docs" / "figures"
TABLES = REPO_ROOT / "docs" / "tables"

# Primary real-robot run for the timing figures.
PRIMARY = "ur3-arm-6dof"

# Curated clean runs for the results table (label, file stem, mapping).
TABLE_RUNS = [
    ("Replay -> UR3 (1-DOF)",      "P1-00-firstcontact",   "lakat -> J3"),
    ("Live OptiTrack -> UR3 (6-DOF)", "ur3-arm-6dof",      "ruka -> 6 zglobova"),
    ("Live OptiTrack -> URSim (1-DOF, puni raspon)", "ursim-live-elbow", "lakat -> J3"),
    (r"Live OptiTrack -> URSim (1-DOF, 0--45$^\circ$)", "ursim-live-elbow-0to45", "lakat -> J3"),
]


def _load_latency_csv(stem: str) -> tuple[np.ndarray, np.ndarray]:
    """Return (t_capture[s], latency_ms) from a results CSV."""
    t_cap, lat = [], []
    with (RESULTS / f"{stem}.csv").open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            t_cap.append(float(row["t_capture"]))
            lat.append(float(row["latency_ms"]))
    return np.asarray(t_cap), np.asarray(lat)


def _fig_latency(lat_ms: np.ndarray) -> None:
    med = float(np.median(lat_ms))
    p95 = float(np.percentile(lat_ms, 95))
    p99 = float(np.percentile(lat_ms, 99))
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    ax.hist(lat_ms, bins=60, range=(0, max(20, p99 * 1.1)),
            color="#4878a8", edgecolor="white", linewidth=0.3)
    for val, lbl, c in ((med, "median", "k"), (p95, "p95", "#d08020"), (p99, "p99", "#b02020")):
        ax.axvline(val, color=c, ls="--", lw=1.3, label=f"{lbl} = {val:.1f} ms")
    ax.set_xlabel("end-to-end latencija [ms]"); ax.set_ylabel("broj uzoraka")
    ax.set_title("Latencija OptiTrack→obrada→UR3 (živi 6-DOF)")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGURES / "latency_hist.png", dpi=130)
    plt.close(fig)
    print(f"  latency_hist.png  (median {med:.1f}, p95 {p95:.1f}, p99 {p99:.1f} ms)")


def _fig_interarrival(t_cap: np.ndarray) -> None:
    dt_ms = np.diff(np.unique(t_cap)) * 1000.0
    dt_ms = dt_ms[(dt_ms > 0) & (dt_ms < 40)]      # drop gaps/duplicates for the view
    mean = float(dt_ms.mean()); std = float(dt_ms.std())
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    ax.hist(dt_ms, bins=50, color="#4a9a6a", edgecolor="white", linewidth=0.3)
    ax.axvline(1000.0 / 120.0, color="k", ls="--", lw=1.3, label="120 Hz (8.33 ms)")
    ax.set_xlabel("razmak između okvira [ms]"); ax.set_ylabel("broj okvira")
    ax.set_title(f"Stabilnost uzorkovanja: {mean:.2f} ± {std:.2f} ms")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGURES / "interarrival_hist.png", dpi=130)
    plt.close(fig)
    print(f"  interarrival_hist.png  ({mean:.2f} ± {std:.2f} ms)")


def _copy(name: str) -> None:
    src = PROCESSED / name
    if src.exists():
        shutil.copyfile(src, FIGURES / name)
        print(f"  {name}  (copied from data/processed)")
    else:
        print(f"  ! {name} missing in data/processed — run its generator first")


def _table() -> None:
    rows = []
    for label, stem, mapping in TABLE_RUNS:
        p = RESULTS / f"{stem}.summary.json"
        if not p.exists():
            continue
        s = json.loads(p.read_text(encoding="utf-8"))
        lat = s["latency"]
        # Trajanje runa = broj primljenih paketa / izmjerena frekvencija prijema
        # (NE latency["n"], koji broji takte kontrolne petlje, ne pakete).
        dur_s = s["rx_received"] / s["rx_rate_hz"] if s["rx_rate_hz"] else 0.0
        rows.append((label, mapping, s["rx_rate_hz"], dur_s, lat["median_ms"],
                     lat["p95_ms"], lat["jitter_ms"], s["rx_loss_pct"]))

    lines = [
        r"\begin{tabular}{llrrrrrr}",
        r"\hline",
        r"Scenarij & Mapiranje & Hz & traj. [s] & med. [ms] & p95 [ms] & jitter [ms] & gubitak [\%] \\",
        r"\hline",
    ]
    arrow = r"$\rightarrow$"
    for label, mapping, hz, dur_s, med, p95, jit, loss in rows:
        label = label.replace("->", arrow)
        mapping = mapping.replace("->", arrow)
        lines.append(f"{label} & {mapping} & {hz:.1f} & {dur_s:.1f} & {med:.1f} & "
                     f"{p95:.1f} & {jit:.1f} & {loss:.1f} \\\\")
    lines += [r"\hline", r"\end{tabular}"]
    (TABLES / "results.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  results.tex  ({len(rows)} runova)")


def main() -> int:
    FIGURES.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("FIGURE I TABLICE ZA RAD -> docs/figures, docs/tables")
    print("=" * 78)

    t_cap, lat = _load_latency_csv(PRIMARY)
    _fig_latency(lat)
    _fig_interarrival(t_cap)
    _copy("step_response.png")
    _copy("filter_comparison.png")
    _table()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
