"""Step / sudden-movement response of the control chain (Var. A, phase 5).

The task asks to analyse system *sensitivity to sudden motion*. A real human
cannot move infinitely fast, but a step input is the worst case: it probes how
the causal filter (lag) and the :class:`SafetyGuard` (rate limit, range clamp)
shape an abrupt command before it reaches the robot.

We drive a synthetic elbow target through the exact same blocks the live
pipeline uses -- ``OneEuroFilter`` (``src/filtering``) then ``SafetyGuard``
(``src/safety/guard.py``) -- at the OptiTrack rate (120 Hz), and record the
raw target, filtered, and safe-commanded angle. Two probes are run:

  * **step**  -- abrupt jump (sudden joint movement),
  * **flick** -- short impulse up then back (tremor-like burst).

Outputs (git-ignored, regenerable): ``data/processed/step_response.csv`` and
``data/processed/step_response.png``.

Usage:
    python -m src.tools.step_response
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.filtering.one_euro import OneEuroFilter
from src.safety.guard import SafetyGuard

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT = REPO_ROOT / "data" / "processed"

FS_HZ = 120.0                 # OptiTrack sampling rate
DT = 1.0 / FS_HZ
# Elbow joint (J3) ceilings from src/config/default.yaml (multi_joint + safety).
MAX_SPEED_DPS = 45.0
RANGE_DPS = 60.0
NOISE_DEG = 0.4               # marker-equivalent measurement noise (1 sigma)


def _run_chain(target_deg: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Push a noisy target through One-Euro + SafetyGuard, sample by sample."""
    rng = np.random.default_rng(seed)
    noisy = target_deg + rng.normal(0.0, NOISE_DEG, size=target_deg.shape)

    oe = OneEuroFilter(freq_hz=FS_HZ, min_cutoff=1.0, beta=0.007, d_cutoff=1.0)
    guard = SafetyGuard(home=0.0, max_joint_speed_dps=MAX_SPEED_DPS,
                        joint_range_dps=RANGE_DPS, signal_timeout_s=0.15)

    filt = np.empty_like(target_deg)
    safe = np.empty_like(target_deg)
    for i, _ in enumerate(target_deg):
        t = i * DT
        f = oe(float(noisy[i]), t)
        d = guard.step(np.radians(f), DT, signal_age_s=0.0)
        filt[i] = f
        safe[i] = np.degrees(d.angle)
    return filt, safe


def _settling_time_s(t: np.ndarray, y: np.ndarray, final: float,
                     band_frac: float = 0.02) -> float:
    """First time after which |y - final| stays within band_frac*|final|."""
    band = max(abs(final) * band_frac, 0.2)
    outside = np.abs(y - final) > band
    idx = np.where(outside)[0]
    if idx.size == 0:
        return 0.0
    return float(t[idx[-1]])


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("STEP / NAGLI POKRET — odziv lanca filter + SafetyGuard (lakat J3, 120 Hz)")
    print("=" * 78)
    print(f"  rate-limit {MAX_SPEED_DPS:.0f} °/s, raspon ±{RANGE_DPS:.0f}°, "
          f"One-Euro(min_cutoff=1.0, beta=0.007), šum {NOISE_DEG} ° RMS\n")

    n = int(2.0 * FS_HZ)              # 2 s window
    t = np.arange(n) * DT

    # --- Probe 1: step (sudden movement) ---
    step_amp = 40.0
    step = np.zeros(n)
    step[t >= 0.5] = step_amp
    step_filt, step_safe = _run_chain(step, seed=1)

    # --- Probe 2: flick (impulse: up then back) ---
    flick = np.zeros(n)
    flick[(t >= 0.5) & (t < 0.7)] = 35.0
    flick_filt, flick_safe = _run_chain(flick, seed=2)

    # --- Metrics on the step ---
    cmd_rate = np.abs(np.diff(step_safe)) / DT       # °/s actually commanded
    settle = _settling_time_s(t, step_safe, step_amp) - 0.5
    overshoot = max(0.0, step_safe.max() - step_amp)
    print("STEP (skok 0 -> 40°):")
    print(f"  maks. komandirana brzina  : {cmd_rate.max():.1f} °/s  "
          f"(strop {MAX_SPEED_DPS:.0f} °/s)")
    print(f"  rate-limit aktivan         : {100*np.mean(cmd_rate > MAX_SPEED_DPS - 1):.0f}% uzoraka "
          f"odmah nakon skoka")
    print(f"  overshoot                  : {overshoot:.2f}°")
    print(f"  vrijeme smirivanja (±2%)   : {settle*1000:.0f} ms")
    flick_peak = flick_safe.max()
    print("\nFLICK (impuls 35° / 0.2 s):")
    print(f"  vršni prijenos na robota   : {flick_peak:.1f}° (od 35° ulaza) "
          f"-> kratak impuls je prigušen rate-limitom\n")

    # --- CSV ---
    csv_path = OUT / "step_response.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["t_s",
                    "step_target_deg", "step_filtered_deg", "step_safe_deg",
                    "flick_target_deg", "flick_filtered_deg", "flick_safe_deg"])
        for i in range(n):
            w.writerow([f"{t[i]:.5f}",
                        f"{step[i]:.4f}", f"{step_filt[i]:.4f}", f"{step_safe[i]:.4f}",
                        f"{flick[i]:.4f}", f"{flick_filt[i]:.4f}", f"{flick_safe[i]:.4f}"])
    print(f"CSV  -> {csv_path}")

    # --- Figure ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    ax1.plot(t, step, color="0.7", lw=1.0, label="ulaz (cilj)")
    ax1.plot(t, step_filt, "b-", lw=1.2, label="nakon filtra")
    ax1.plot(t, step_safe, "r-", lw=1.6, label="sigurnosno (na robot)")
    ax1.set_title(f"Skok 0→{step_amp:.0f}° — rate-limit {MAX_SPEED_DPS:.0f} °/s")
    ax1.set_xlabel("vrijeme [s]"); ax1.set_ylabel("kut zgloba [°]")
    ax1.legend(loc="lower right"); ax1.grid(alpha=0.3)

    ax2.plot(t, flick, color="0.7", lw=1.0, label="ulaz (cilj)")
    ax2.plot(t, flick_filt, "b-", lw=1.2, label="nakon filtra")
    ax2.plot(t, flick_safe, "r-", lw=1.6, label="sigurnosno (na robot)")
    ax2.set_title("Impuls (flick) 35° / 0.2 s — prigušenje")
    ax2.set_xlabel("vrijeme [s]"); ax2.set_ylabel("kut zgloba [°]")
    ax2.legend(loc="upper right"); ax2.grid(alpha=0.3)

    fig.tight_layout()
    png_path = OUT / "step_response.png"
    fig.savefig(png_path, dpi=130)
    print(f"PNG  -> {png_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
