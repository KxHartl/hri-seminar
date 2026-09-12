"""Generate publication-ready scientific figures for the FSB HRI seminar report.

Creates figures in docs/figures/:
  * setup_photo.jpg            -- Laboratory setup photo (human operator + UR3e robot)
  * markers_detail_crop.jpg    -- Cropped detail of the marker layout on the arm
  * markers_digital_twin.png   -- 2-panel composite of arm markers + Motive 3D rigid bodies
  * signal_quality.pdf/.png    -- Sampling stability + processing latency (2 panels)
  * tracking_6dof_time.pdf/.png -- Six-channel time-series tracking (T1a)
  * filter_real_robot.pdf/.png -- Real-robot filter comparison, 2x2 (T2a..T2d)
  * safety_events.pdf/.png     -- 4-panel proof of the safety layers (T3a..T3d)
  * dynamics.pdf/.png          -- Added-delay sweep + step/impulse response (2 panels)
  * packet_loss_stability.pdf/.png -- Packet loss vs signal age & tracking error (T5)

Standardized design system:
  * Font: Times New Roman / TeX Gyre Termes (serif, STIX mathtext)
  * Widths: 1-col = 3.35 in, 2-col = 6.90 in
  * Colors: Human = #7f7f7f (dotted), Command = #1f77b4 (solid),
            Actual UR3e = #d62728 (dashed), Safety Limit = #2ca02c (dashdot)

Usage:
    python -m src.tools.generate_report_figures
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
from PIL import Image

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = REPO_ROOT / "data/raw/lab_session_01092026_020000/telemetry"
CAMERA_DIR = REPO_ROOT / "data" / "lab_testing_camera"
FIGURES_DIR = REPO_ROOT / "docs" / "figures"

from src.tools.track_analysis import (
    _fill_holds, _hold_mask, _joint_mapping, _scale,
)

# Standardized semantic color palette:
COLOR_HUMAN = "#7f7f7f"       # Gray dotted: operator arm angle (mapped)
COLOR_CMD = "#1f77b4"         # Deep Blue solid: robot command trajectory
COLOR_ACTUAL = "#d62728"      # Crimson Red dashed: real UR3e robot response
COLOR_LIMIT = "#2ca02c"       # Forest Green dash-dot: safety limits/thresholds
COLOR_EVENT_SPAN = "#fee08b"  # Amber warning background span
COLOR_EVENT_LINE = "#d95f02"  # Orange trigger line

# Histogram / metric colors:
COLOR_HIST_PRIMARY = "#2b5c8f"    # Deep Navy Blue
COLOR_HIST_SECONDARY = "#2ca25f"  # Emerald Green
COLOR_PERCENTILE_MED = "#111111"  # Black
COLOR_PERCENTILE_P95 = "#d95f02"  # Orange
COLOR_PERCENTILE_P99 = "#7570b3"  # Purple

# Set publication-ready typography matching LaTeX document:
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "TeX Gyre Termes", "DejaVu Serif", "serif"],
    "mathtext.fontset": "stix",
    "font.size": 8.5,
    "axes.labelsize": 8.5,
    "axes.titlesize": 9.0,
    "xtick.labelsize": 8.0,
    "ytick.labelsize": 8.0,
    "legend.fontsize": 7.5,
    "figure.titlesize": 10.0,
    "lines.linewidth": 1.2,
    "grid.alpha": 0.35,
    "grid.linestyle": "--",
})


def _save_fig(fig: plt.Figure, name: str, dpi: int = 200) -> None:
    fig.savefig(FIGURES_DIR / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(FIGURES_DIR / f"{name}.png", dpi=dpi, bbox_inches="tight")
    print(f"Generated {name}.pdf and {name}.png")


def _load_track_csv(stem: str) -> dict[str, np.ndarray]:
    p = RESULTS_DIR / f"{stem}.track.csv"
    if not p.exists():
        raise FileNotFoundError(f"Missing track CSV: {p}")
    with p.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}


def _load_latency_csv(stem: str) -> tuple[np.ndarray, np.ndarray]:
    p = RESULTS_DIR / f"{stem}.csv"
    if not p.exists():
        raise FileNotFoundError(f"Missing latency CSV: {p}")
    t_cap, lat = [], []
    with p.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            t_cap.append(float(row["t_capture"]))
            lat.append(float(row["latency_ms"]))
    return np.asarray(t_cap), np.asarray(lat)


_CFG_CACHE: dict | None = None


def _human_curve(cols: dict, jkey: str) -> np.ndarray:
    """The operator's arm angle expressed in robot-joint degrees.

    Plotting ``in_J*_deg`` directly is misleading twice over: it is recorded
    before the mapping gain and inversion (so a joint with gain 2.2 looks half
    the size and an inverted one runs backwards), and it is written as an exact
    zero on ticks where no channel value arrived, which drops the curve to the
    axis dozens of times per second. Both are corrected here exactly as
    :mod:`src.tools.track_analysis` does.
    """
    global _CFG_CACHE
    if _CFG_CACHE is None:
        import yaml
        _CFG_CACHE = yaml.safe_load(
            (REPO_ROOT / "src" / "config" / "default.yaml").read_text(encoding="utf-8"))
    mapping = _joint_mapping(_CFG_CACHE)
    jn = int(jkey[1:])
    raw = cols[f"in_{jkey}_deg"]
    filt = cols.get(f"filt_{jkey}_deg", raw)
    return _scale(_fill_holds(raw, _hold_mask(raw, filt)), mapping.get(jn))


def process_setup_photos() -> None:
    """Copies and optimizes the lab photos used in the report."""
    src_setup = CAMERA_DIR / "person_and_robot.jpg"
    dst_setup = FIGURES_DIR / "setup_photo.jpg"
    if src_setup.exists():
        img = Image.open(src_setup)
        img.save(dst_setup, "JPEG", quality=90, optimize=True)
        print(f"Generated {dst_setup}")

    src_markers = CAMERA_DIR / "markers_left.jpg"
    dst_markers = FIGURES_DIR / "markers_detail_crop.jpg"
    if src_markers.exists():
        img = Image.open(src_markers).crop((500, 1140, 3560, 2180))
        img.save(dst_markers, "JPEG", quality=88, optimize=True)
        print(f"Generated {dst_markers}")

    src_colored = CAMERA_DIR / "markers_colored.png"
    src_motive = REPO_ROOT / "data" / "optitrack" / "screen_recording" / "optitrack_rigidbodys.png"
    dst_twin = FIGURES_DIR / "markers_digital_twin.png"
    if src_colored.exists() and src_motive.exists():
        cam = Image.open(src_colored).convert("RGB")
        mot = Image.open(src_motive).convert("RGB")
        arm_crop = cam.crop((750, 100, 1750, 3600)).rotate(90, expand=True)
        mot_crop = mot.crop((450, 480, 1200, 820))

        fig, axes = plt.subplots(2, 1, figsize=(6.90, 3.3))
        axes[0].imshow(arm_crop)
        axes[0].set_title(
            "a) Fizički raspored markera: 5 po segmentu (cijan = nadlaktica, magenta = podlaktica, narančasto = šaka)",
            fontsize=8.5, pad=3)
        axes[0].axis("off")

        axes[1].imshow(mot_crop)
        axes[1].set_title(
            "b) 3D rekonstrukcija krutih tijela s koordinatnim osima i mrežama u sustavu OptiTrack Motive",
            fontsize=8.5, pad=3)
        axes[1].axis("off")

        plt.tight_layout()
        fig.savefig(dst_twin, dpi=200, bbox_inches="tight")
        plt.close(fig)
        print(f"Generated {dst_twin}")


PUBLIC_ID = {
    "T-02": "T1a", "T-03": "T1b",
    "T-04": "T2a", "T-05": "T2b", "T-06": "T2c", "T-07": "T2d",
    "T-08": "T3a", "T-09": "T3b", "T-10": "T3c", "T-12a": "T3d", "T-11": "T3e",
    "T-13a": "T4a", "T-13b": "T4b", "T-13c": "T4c", "T-13d": "T4d", "T-13e": "T4e",
    "T-14": "T5a", "T-15": "T5b", "T-16": "T5c", "T-17": "T5d", "T-18": "T5e",
    "T-20": "T6",
}


def _hr(x: float, nd: int = 1) -> str:
    """Croatian decimal comma, for numbers baked into figure labels."""
    return f"{x:.{nd}f}".replace(".", ",")


def fig_signal_quality() -> None:
    """Sampling stability and processing latency, side by side."""
    t_cap, lat_ms = _load_latency_csv("T-02")
    med = float(np.median(lat_ms))
    p95 = float(np.percentile(lat_ms, 95))
    p99 = float(np.percentile(lat_ms, 99))

    dt_ms = np.diff(np.unique(t_cap)) * 1000.0
    dt_ms = dt_ms[(dt_ms > 0) & (dt_ms < 30)]
    mean_dt, std_dt = float(dt_ms.mean()), float(dt_ms.std())

    fig, axes = plt.subplots(2, 1, figsize=(3.35, 3.4))

    ax = axes[0]
    ax.hist(dt_ms, bins=45, color=COLOR_HIST_SECONDARY, edgecolor="white", linewidth=0.4)
    ax.axvline(1000.0 / 120.0, color="#111111", ls="--", lw=1.2,
               label=r"120 Hz ($8{,}33$ ms)")
    ax.set_xlabel(r"Razmak između okvira $\Delta t$ [ms]")
    ax.set_ylabel("Broj okvira")
    ax.set_title(f"a) Stabilnost uzorkovanja: {_hr(mean_dt, 2)} $\\pm$ {_hr(std_dt, 2)} ms", pad=2)
    ax.legend(loc="upper right", framealpha=0.9)
    ax.grid(True)

    ax = axes[1]
    ax.hist(lat_ms, bins=50, range=(0, max(20, p99 * 1.15)),
            color=COLOR_HIST_PRIMARY, edgecolor="white", linewidth=0.4)
    ax.axvline(med, color="#111111", ls="--", lw=1.2, label=f"medijan = {_hr(med)} ms")
    ax.axvline(p95, color=COLOR_PERCENTILE_P95, ls="--", lw=1.2, label=f"p95 = {_hr(p95)} ms")
    ax.axvline(p99, color=COLOR_PERCENTILE_P99, ls="--", lw=1.2, label=f"p99 = {_hr(p99)} ms")
    ax.set_xlabel("Latencija obrade [ms]")
    ax.set_ylabel("Broj taktova")
    ax.set_title("b) Latencija obrade po taktu", pad=2)
    ax.legend(loc="upper right", framealpha=0.9)
    ax.grid(True)

    fig.tight_layout()
    _save_fig(fig, "signal_quality", dpi=200)
    plt.close(fig)


def fig_tracking_6dof_time() -> None:
    """Six-channel tracking over time for the natural-tempo fidelity run."""
    cols = _load_track_csv("T-02")
    t = cols["t_s"]
    mask = (t >= 5.0) & (t <= 25.0)
    t_win = t[mask] - 5.0

    joint_labels = [
        ("J1", "J1: baza — zakret ramena"),
        ("J2", "J2: rame — nagib"),
        ("J3", "J3: lakat — fleksija"),
        ("J4", "J4: zapešće 1 — fleksija"),
        ("J5", "J5: zapešće 2 — devijacija"),
        ("J6", "J6: zapešće 3 — aksijalna rotacija"),
    ]

    fig, axes = plt.subplots(3, 2, figsize=(6.90, 4.4), sharex=True)
    axes_flat = axes.flatten()

    for idx, (jkey, label) in enumerate(joint_labels):
        ax = axes_flat[idx]
        in_deg = _human_curve(cols, jkey)[mask]
        cmd_deg = cols[f"cmd_{jkey}_deg"][mask]
        act_deg = cols[f"act_{jkey}_deg"][mask]

        ax.plot(t_win, in_deg, color=COLOR_HUMAN, ls=":", lw=1.1, alpha=0.85,
                label="kut ruke, preslikan")
        ax.plot(t_win, cmd_deg, color=COLOR_CMD, ls="-", lw=1.3, label="naredba robotu")
        ax.plot(t_win, act_deg, color=COLOR_ACTUAL, ls="--", lw=1.2, label="stvarni kut robota")
        ax.set_ylabel(r"Kut [$^\circ$]")
        ax.set_title(label, pad=2)
        ax.grid(True)
        if idx == 0:
            ax.legend(loc="upper right", framealpha=0.9, fontsize=7.2)

    axes[2, 0].set_xlabel("Vrijeme [s]")
    axes[2, 1].set_xlabel("Vrijeme [s]")
    fig.suptitle(
        "Oponašanje pokreta ruke sa šest stupnjeva slobode, zglob na zglob "
        f"(pokus {PUBLIC_ID['T-02']})", y=0.99)
    fig.tight_layout()
    _save_fig(fig, "tracking_6dof_time", dpi=200)
    plt.close(fig)


def fig_filter_real_robot() -> None:
    """Four filters on the same motion, laid out 2x2 with consistent semantic lines."""
    runs = [
        ("T-04", "One-Euro filtar"),
        ("T-05", "bez filtra"),
        ("T-06", "Butterworth, 2. reda"),
        ("T-07", "eksponencijalni pomični prosjek"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(6.90, 3.6), sharex=True, sharey=True)
    axes_flat = axes.flatten()

    for idx, (stem, name) in enumerate(runs):
        cols = _load_track_csv(stem)
        t = cols["t_s"]
        mask = (t >= 4.0) & (t <= 16.0)
        t_win = t[mask] - 4.0
        ax = axes_flat[idx]
        ax.plot(t_win, _human_curve(cols, "J3")[mask], color=COLOR_HUMAN, ls=":", lw=1.0,
                alpha=0.8, label="kut ruke, preslikan")
        ax.plot(t_win, cols["cmd_J3_deg"][mask], color=COLOR_CMD, lw=1.3, label="naredba robotu")
        ax.plot(t_win, cols["act_J3_deg"][mask], color=COLOR_ACTUAL, ls="--", lw=1.1,
                label="stvarni kut robota")
        ax.set_title(f"{chr(97 + idx)}) {name} ({PUBLIC_ID[stem]})", pad=2)
        ax.grid(True)
        if idx % 2 == 0:
            ax.set_ylabel(r"Kut J3 [$^\circ$]")
        if idx >= 2:
            ax.set_xlabel("Vrijeme [s]")
        if idx == 0:
            ax.legend(loc="upper right", framealpha=0.9, fontsize=7.2)

    fig.suptitle("Usporedba filtara na stvarnom robotu UR3e — zglob J3 (lakat)", y=0.99)
    fig.tight_layout()
    _save_fig(fig, "filter_real_robot", dpi=200)
    plt.close(fig)


def fig_safety_events() -> None:
    """Each safety layer, with standard semantic colors across all panels."""
    fig, axes = plt.subplots(2, 2, figsize=(6.90, 3.6))

    # a) joint speed limit -- J1
    cols = _load_track_csv("T-08")
    t = cols["t_s"]
    ax = axes[0, 0]
    ax.plot(t, _human_curve(cols, "J1"), color=COLOR_HUMAN, ls=":", lw=1.0,
            label="kut ruke, preslikan")
    ax.plot(t, cols["cmd_J1_deg"], color=COLOR_CMD, lw=1.3,
            label=r"naredba uz ogr. $25^\circ/\text{s}$")
    ax.plot(t, cols["act_J1_deg"], color=COLOR_ACTUAL, ls="--", lw=1.1,
            label="stvarni kut robota")
    ax.set_ylabel(r"Kut J1 [$^\circ$]")
    ax.set_title(f"a) Ograničenje brzine zgloba ({PUBLIC_ID['T-08']}, zglob J1)", pad=2)
    ax.legend(loc="upper right", fontsize=7.0, framealpha=0.9)
    ax.grid(True)

    # b) joint range limit -- J1
    cols = _load_track_csv("T-09")
    t = cols["t_s"]
    ax = axes[0, 1]
    ax.plot(t, _human_curve(cols, "J1"), color=COLOR_HUMAN, ls=":", lw=1.0,
            label="kut ruke, preslikan")
    ax.axhline(25.0, color=COLOR_LIMIT, ls="-.", lw=1.1,
               label=r"granica $\pm 25^\circ$")
    ax.axhline(-25.0, color=COLOR_LIMIT, ls="-.", lw=1.1)
    ax.plot(t, cols["cmd_J1_deg"], color=COLOR_CMD, lw=1.3, label="zasićena naredba")
    ax.plot(t, cols["act_J1_deg"], color=COLOR_ACTUAL, ls="--", lw=1.1,
            label="stvarni kut robota")
    ax.set_ylabel(r"Kut J1 [$^\circ$]")
    ax.set_title(f"b) Ograničenje raspona gibanja ({PUBLIC_ID['T-09']}, zglob J1)", pad=2)
    ax.legend(loc="upper right", fontsize=7.0, framealpha=0.9)
    ax.grid(True)

    # c) marker occlusion -- J1
    cols = _load_track_csv("T-10")
    t = cols["t_s"]
    mask = (t >= 5.0) & (t <= 20.0)
    ax = axes[1, 0]
    ax.axvspan(11.37, 16.32, color=COLOR_EVENT_SPAN, alpha=0.35, label="okluzija markera (5,0 s)")
    ax.plot(t[mask], _human_curve(cols, "J1")[mask], color=COLOR_HUMAN, ls=":", lw=1.0,
            label="kut ruke, preslikan")
    ax.plot(t[mask], cols["cmd_J1_deg"][mask], color=COLOR_CMD, lw=1.3,
            label="zadržana naredba")
    ax.plot(t[mask], cols["act_J1_deg"][mask], color=COLOR_ACTUAL, ls="--", lw=1.1,
            label="stvarni kut robota")
    ax.set_xlabel("Vrijeme [s]")
    ax.set_ylabel(r"Kut J1 [$^\circ$]")
    ax.set_title(f"c) Okluzija markera ({PUBLIC_ID['T-10']}, zglob J1)", pad=2)
    ax.legend(loc="lower left", fontsize=7.0, framealpha=0.9)
    ax.grid(True)

    # d) software stop at t = 10 s -- J1
    cols = _load_track_csv("T-12a")
    t = cols["t_s"]
    mask = (t >= 5.0) & (t <= 18.0)
    ax = axes[1, 1]
    ax.plot(t[mask], _human_curve(cols, "J1")[mask], color=COLOR_HUMAN, ls=":", lw=1.0,
            label="kut ruke, preslikan")
    ax.plot(t[mask], cols["cmd_J1_deg"][mask], color=COLOR_CMD, lw=1.3,
            label="zamrznuta naredba")
    ax.plot(t[mask], cols["act_J1_deg"][mask], color=COLOR_ACTUAL, ls="--", lw=1.1,
            label="stvarni kut robota")
    ax.axvline(10.0, color="#f1b500", ls="-", lw=1.6, label="okidanje ($t=10$ s)")
    ax.set_xlabel("Vrijeme [s]")
    ax.set_ylabel(r"Kut J1 [$^\circ$]")
    ax.set_title(f"d) Programsko zaustavljanje ({PUBLIC_ID['T-12a']}, zglob J1)", pad=2)
    ax.legend(loc="upper right", fontsize=7.0, framealpha=0.9)
    ax.grid(True)

    fig.suptitle("Djelovanje sigurnosnih slojeva na stvarnom robotu UR3e (zglob J1)", y=0.99)
    fig.tight_layout()
    _save_fig(fig, "safety_events", dpi=200)
    plt.close(fig)


def fig_dynamics() -> None:
    """Two dynamic tests in one figure: added delay, and response to a step."""
    runs = ["T-13a", "T-13b", "T-13c", "T-13d", "T-13e"]
    added_ms = [0, 50, 100, 200, 400]
    measured_med, measured_p99, holds = [], [], []

    for stem in runs:
        net = json.loads((RESULTS_DIR / f"{stem}.summary.json").read_text(encoding="utf-8"))
        trk = json.loads((RESULTS_DIR / f"{stem}.track.summary.json").read_text(encoding="utf-8"))
        measured_med.append(net["latency"]["median_ms"])
        measured_p99.append(net["latency"]["p99_ms"])
        n = trk["n"]
        holds.append(100.0 * trk["joints"]["J3"]["safety_events"].get("halted_ticks", 0) / n)

    fig, (ax1, axb) = plt.subplots(1, 2, figsize=(6.90, 2.7))

    c1 = COLOR_HIST_PRIMARY
    ax1.set_xlabel("Dodano mrežno kašnjenje [ms]")
    ax1.set_ylabel("Izmjerena latencija obrade [ms]", color=c1)
    ax1.plot(added_ms, measured_med, marker="o", color=c1, lw=1.4, label="medijan")
    ax1.plot(added_ms, measured_p99, marker="v", ls=":", color=c1, lw=1.1, alpha=0.75,
             label="p99")
    ax1.tick_params(axis="y", labelcolor=c1)
    ax1.grid(True)

    ax1.axvspan(0, 100, color="#1a9850", alpha=0.12)
    ax1.axvspan(100, 200, color="#fee08b", alpha=0.20)
    ax1.axvspan(200, 425, color="#d73027", alpha=0.12)
    ax1.text(45, ax1.get_ylim()[1] * 0.93, "kontinuirano", fontsize=6.8, ha="center")
    ax1.text(150, ax1.get_ylim()[1] * 0.93, "oprez", fontsize=6.8, ha="center")
    ax1.text(310, ax1.get_ylim()[1] * 0.93, "pomak i čekanje", fontsize=6.8, ha="center")

    ax2 = ax1.twinx()
    c2 = "#d95f02"
    ax2.set_ylabel("Udio zadržanih taktova [%]", color=c2)
    ax2.plot(added_ms, holds, marker="s", ls="--", color=c2, lw=1.4, label="zadržavanje (red prazan)")
    ax2.tick_params(axis="y", labelcolor=c2)

    ax1.set_xlim(-15, 425)
    ax1.legend(loc="center left", fontsize=6.8, framealpha=0.9)
    ax2.legend(loc="lower right", fontsize=6.8, framealpha=0.9)
    ax1.set_title("a) Utjecaj dodanog kašnjenja", fontsize=9.0)

    step = _load_step_response()
    if step is not None:
        ts = step["t_s"]
        axb.plot(ts, step["step_target_deg"], color=COLOR_HUMAN, ls=":", lw=1.1, label="zadani skok")
        axb.plot(ts, step["step_filtered_deg"], color=COLOR_CMD, lw=1.3, label="nakon filtra")
        axb.plot(ts, step["step_safe_deg"], color=COLOR_ACTUAL, ls="--", lw=1.3,
                 label="nakon sigurnosnog sloja")
        axb.plot(ts, step["flick_filtered_deg"], color=COLOR_CMD, ls=":", lw=1.1,
                 label="impuls, nakon filtra")
        axb.plot(ts, step["flick_safe_deg"], color=COLOR_ACTUAL, ls="-.", lw=1.1,
                 label="impuls, nakon sigurnosnog sloja")
        axb.set_xlabel("Vrijeme [s]")
        axb.set_ylabel(r"Kut zgloba [$^\circ$]")
        axb.legend(loc="lower right", fontsize=6.8, framealpha=0.9)
        axb.grid(True)
    axb.set_title(r"b) Odziv na skok $0\rightarrow40^\circ$ i na impuls", fontsize=9.0)

    fig.tight_layout()
    _save_fig(fig, "dynamics", dpi=200)
    plt.close(fig)


def _load_step_response() -> dict[str, np.ndarray] | None:
    p = REPO_ROOT / "data" / "processed" / "step_response.csv"
    if not p.exists():
        print(f"  (skipping step response: {p} missing -- run src.tools.step_response)")
        return None
    with p.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}


def fig_packet_loss_stability() -> None:
    """Controlled loss sweep: one recording, five drop rates."""
    sweep = REPO_ROOT / "data/processed/packet_loss_sweep_02092026"
    stems = ["L-00", "L-05", "L-10", "L-20", "L-30"]
    target = [0, 5, 10, 20, 30]
    age_p95, rmse = [], []

    for stem in stems:
        net = json.loads((sweep / f"{stem}.summary.json").read_text(encoding="utf-8"))
        trk = json.loads((sweep / f"{stem}.track.summary.json").read_text(encoding="utf-8"))
        age_p95.append(net["signal_age_ms"]["p95_ms"])
        vals = [trk["joints"][f"J{k}"]["scaled_input_to_actual"]["rmse_aligned_deg"]
                for k in range(1, 7)]
        rmse.append(sum(vals) / len(vals))

    fig, ax1 = plt.subplots(figsize=(5.6, 3.2))
    c1 = COLOR_HIST_SECONDARY
    ax1.set_xlabel("Gubitak UDP paketa [%]")
    ax1.set_ylabel("Starost signala, p95 [ms]", color=c1)
    ax1.plot(target, age_p95, marker="o", color=c1, lw=1.4)
    ax1.tick_params(axis="y", labelcolor=c1)
    ax1.grid(True)
    ax1.axhline(150.0, color="#999999", ls=":", lw=1.0)
    ax1.text(1, 152, "prag zadržavanja izlaza, 150 ms", fontsize=7, color="#666666")

    ax2 = ax1.twinx()
    c2 = COLOR_PERCENTILE_P99
    ax2.set_ylabel(r"Pogreška praćenja [$^\circ$]", color=c2)
    ax2.plot(target, rmse, marker="^", ls="--", color=c2, lw=1.4)
    ax2.tick_params(axis="y", labelcolor=c2)

    ax1.set_title("Otpornost na gubitak paketa (kontrolirani niz nad istom snimkom)", pad=2)
    fig.tight_layout()
    _save_fig(fig, "packet_loss_stability", dpi=200)
    plt.close(fig)


def main() -> int:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    print("Generating all publication-ready figures for seminar...")
    process_setup_photos()
    fig_signal_quality()
    fig_tracking_6dof_time()
    fig_filter_real_robot()
    fig_safety_events()
    fig_dynamics()
    fig_packet_loss_stability()
    print("All figures successfully created in docs/figures/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
