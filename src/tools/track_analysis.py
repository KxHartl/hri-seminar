"""Tracking-fidelity metrics from a track CSV (see :mod:`src.pipeline.tracklog`).

Answers the question the timing logs cannot: *how faithfully does the robot
reproduce the arm?* For every driven joint it reports

  * **RMSE, lag and correlation** for four signal pairs, which answer different
    questions and must not be confused:

    ``scaled_input_to_actual``
        the human angle *after* the configured ``arm_mapping`` gain and
        inversion, against the angle the robot reached. This is the fidelity of
        the mimicry -- the paper's central claim.
    ``target_to_actual``
        the mapped setpoint before the safety layer, against what the robot
        reached: fidelity of execution, including whatever the guard clamped.
    ``command_to_actual``
        the post-safety command against the measured angle. This is the UR3e
        servo following its *own* setpoint, not the human; it lands near
        ``servoj.lookahead_time`` and says nothing about tracking the arm.
    ``input_to_command`` / ``input_to_actual``
        the raw, pre-gain channel against the robot. Kept for continuity, but
        the gain (2.2 on shoulder pitch, 1.5 on elbow) and the inversions make
        these large and sometimes negatively correlated by construction.

  * peak deviation, and RMSE recomputed after removing the estimated lag, so a
    pure phase shift is not counted as an amplitude error,
  * how many ticks each safety layer engaged on.

Outputs, next to the input file: ``<name>.summary.json`` and an overlay figure
``<name>.png`` showing input vs command vs actual through time.

Usage:
    python -m src.tools.track_analysis data/raw/lab_session_01092026_020000/telemetry/T-02.track.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml

from src.filtering.analysis import estimate_lag_ms

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "src" / "config" / "default.yaml"

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

_JOINT_RE = re.compile(r"^in_J(\d+)_deg$")
_FLAGS = ("ratelim", "rangeclamp", "halted")


def _load(path: Path) -> tuple[dict[str, np.ndarray], list[int]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise SystemExit(f"Prazan track CSV: {path}")
    cols = {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}
    joints = sorted(int(m.group(1)) for m in
                    (_JOINT_RE.match(k) for k in rows[0]) if m)
    return cols, joints


def _fs_hz(t_s: np.ndarray) -> float:
    if len(t_s) < 2:
        return 0.0
    dt = float(np.median(np.diff(t_s)))
    return 1.0 / dt if dt > 0 else 0.0


def _pair(ref: np.ndarray, out: np.ndarray, fs: float) -> dict:
    """Error metrics for one signal pair, with and without the phase shift.

    ``rmse_deg`` compares the two series sample by sample, so a system that
    tracks perfectly but late still scores badly. ``rmse_aligned_deg`` shifts
    ``out`` back by the estimated lag first and therefore isolates the amplitude
    error. Reporting only the first -- as the earlier tables did -- charges the
    servo's own 112 ms lookahead to tracking accuracy.
    """
    err = out - ref
    lag = float(estimate_lag_ms(ref, out, fs)) if fs else float("nan")
    entry = {
        "rmse_deg": float(np.sqrt(np.mean(err ** 2))),
        "max_abs_dev_deg": float(np.max(np.abs(err))),
        "lag_ms": lag,
        "corr": float(np.corrcoef(ref, out)[0, 1]) if np.std(ref) and np.std(out) else 0.0,
    }
    k = 0 if (not fs or math.isnan(lag)) else int(round(lag * fs / 1e3))
    if 0 < k < len(ref) - 10:
        aligned = out[k:] - ref[: len(ref) - k]
        entry["rmse_aligned_deg"] = float(np.sqrt(np.mean(aligned ** 2)))
    else:
        entry["rmse_aligned_deg"] = entry["rmse_deg"]
    return entry


def _joint_mapping(config: dict) -> dict[int, dict]:
    """``arm_mapping`` keyed by the 1-based joint number the track CSV uses.

    The log stores the human channel *before* gain and inversion but the robot
    columns *after* them, so every comparison between the two needs these
    numbers. Falls back to the single-joint ``mapping`` block for 1-DOF runs.
    """
    out: dict[int, dict] = {}
    for m in config.get("arm_mapping", []) or []:
        out[int(m["joint"]) + 1] = {
            "channel": m.get("channel", ""),
            "gain": float(m.get("gain", 1.0)),
            "invert": bool(m.get("invert", False)),
            "offset_deg": math.degrees(float(m.get("offset_rad", 0.0))),
        }
    mp = config.get("mapping") or {}
    if "joint_index" in mp:
        out.setdefault(int(mp["joint_index"]) + 1, {
            "channel": "flexion",
            "gain": float(mp.get("gain", 1.0)),
            "invert": bool(mp.get("invert", False)),
            "offset_deg": math.degrees(float(mp.get("offset_from_home_rad", 0.0))),
        })
    return out


def _scale(raw: np.ndarray, mapping: dict | None) -> np.ndarray:
    """Human channel expressed in robot-joint degrees (gain, inversion, offset)."""
    if not mapping:
        return raw
    sign = -1.0 if mapping["invert"] else 1.0
    return mapping["gain"] * sign * raw + mapping["offset_deg"]


def _hold_mask(raw: np.ndarray, filt: np.ndarray) -> np.ndarray:
    """Ticks on which the control loop received no channel value and held.

    ``_multi_joint_loop`` writes ``in = filt = 0`` and reuses the previous target
    whenever the newest frame carries no value for that channel. The filter
    output is never exactly zero while data is flowing, so the pair of exact
    zeros identifies those ticks unambiguously.

    They are not measurements and must not enter an RMSE: on the September runs
    they are 41-75 % of all ticks, which is why the arm signal reached the
    controller at 31-73 Hz rather than the 120 Hz Motive streams at.
    """
    mask = (raw == 0.0) & (filt == 0.0)
    mask[0] = False
    return mask


def _fill_holds(x: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Carry the last received value across hold ticks, as the pipeline did."""
    if not mask.any():
        return x
    out = x.copy()
    idx = np.where(~mask, np.arange(len(x)), 0)
    np.maximum.accumulate(idx, out=idx)
    return out[idx]


def analyse(path: Path, config: dict | None = None) -> dict:
    cols, joints = _load(path)
    if config is None:
        config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    mapping = _joint_mapping(config)
    t = cols["t_s"]
    fs = _fs_hz(t)
    out: dict = {
        "file": path.name,
        "n": int(len(t)),
        "duration_s": round(float(t[-1] - t[0]), 3),
        "effective_rate_hz": round(fs, 1),
        "joints": {},
    }
    for jn in joints:
        raw = cols[f"in_J{jn}_deg"]
        cmd = cols[f"cmd_J{jn}_deg"]
        mp = mapping.get(jn)
        filt = cols.get(f"filt_J{jn}_deg", raw)
        hold = _hold_mask(raw, filt)
        raw = _fill_holds(raw, hold)
        scaled = _scale(raw, mp)
        entry: dict = {
            "hold_pct": round(100.0 * float(hold.mean()), 1),
            "input_update_rate_hz": round(fs * (1.0 - float(hold.mean())), 1),
            "mapping": mp or {"channel": "", "gain": 1.0, "invert": False, "offset_deg": 0.0},
            "range_in_deg": [round(float(raw.min()), 2), round(float(raw.max()), 2)],
            "range_scaled_in_deg": [round(float(scaled.min()), 2), round(float(scaled.max()), 2)],
            "range_cmd_deg": [round(float(cmd.min()), 2), round(float(cmd.max()), 2)],
            "input_to_command": _pair(raw, cmd, fs),
        }
        if f"target_J{jn}_deg" in cols:
            entry["scaled_input_to_target"] = _pair(scaled, cols[f"target_J{jn}_deg"], fs)
        act_key = f"act_J{jn}_deg"
        if act_key in cols:
            act = cols[act_key]
            entry["scaled_input_to_actual"] = _pair(scaled, act, fs)
            if f"target_J{jn}_deg" in cols:
                entry["target_to_actual"] = _pair(cols[f"target_J{jn}_deg"], act, fs)
            entry["input_to_actual"] = _pair(raw, act, fs)
            entry["command_to_actual"] = _pair(cmd, act, fs)
        entry["safety_events"] = {
            f"{f}_ticks": int(cols[f"{f}_J{jn}"].sum()) for f in _FLAGS
            if f"{f}_J{jn}" in cols
        }
        out["joints"][f"J{jn}"] = entry
    return out


def plot(path: Path, cols: dict, joints: list[int]) -> Path:
    t = cols["t_s"]
    n = len(joints)
    fig, axes = plt.subplots(n, 1, figsize=(9, 2.2 * n + 0.8), sharex=True, squeeze=False)
    for ax, jn in zip(axes[:, 0], joints):
        ax.plot(t, cols[f"in_J{jn}_deg"], lw=0.8, alpha=0.55, label="ulaz (ruka)")
        ax.plot(t, cols[f"cmd_J{jn}_deg"], lw=1.3, label="naredba robotu")
        if f"act_J{jn}_deg" in cols:
            ax.plot(t, cols[f"act_J{jn}_deg"], lw=1.0, ls="--", label="stvarni kut robota")
        ax.set_ylabel(f"J{jn} [°]")
        ax.grid(alpha=0.3)
    axes[0, 0].legend(loc="upper right", fontsize=8)
    axes[-1, 0].set_xlabel("vrijeme [s]")
    fig.suptitle(f"Vjernost praćenja — {path.name}")
    fig.tight_layout()
    out_png = path.with_suffix(".png")
    fig.savefig(out_png, dpi=130)
    plt.close(fig)
    return out_png


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Vjernost praćenja iz track CSV-a")
    ap.add_argument("track_csv", help="npr. data/raw/lab_session_01092026_020000/telemetry/T-02.track.csv")
    ap.add_argument("--no-plot", action="store_true")
    args = ap.parse_args(argv)

    path = Path(args.track_csv)
    if not path.exists():
        raise SystemExit(f"Nema datoteke: {path}")

    res = analyse(path)
    summary_path = path.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=" * 78)
    print(f"VJERNOST PRAĆENJA — {path.name}")
    print(f"{res['n']} uzoraka, {res['duration_s']} s, {res['effective_rate_hz']} Hz")
    print("=" * 78)
    def _fmt(pair: dict) -> str:
        lag = pair["lag_ms"]
        lag_s = " n/d " if math.isnan(lag) else f"{lag:6.1f}"
        return (f"RMSE {pair['rmse_deg']:6.2f}° "
                f"(poravnato {pair['rmse_aligned_deg']:5.2f}°)  "
                f"lag {lag_s} ms  r={pair['corr']:+.3f}")

    for jname, e in res["joints"].items():
        mp = e.get("mapping", {})
        gain_s = f"gain {mp.get('gain', 1.0):.2f}" + (" invert" if mp.get("invert") else "")
        print("")
        print(f"{jname} [{mp.get('channel', '')}, {gain_s}]  ulaz "
              f"{e['range_scaled_in_deg'][0]:+.1f}..{e['range_scaled_in_deg'][1]:+.1f}° (mapirano)")
        if "scaled_input_to_actual" in e:
            print(f"  ruka   -> stvarno (vjernost mimikrije) : {_fmt(e['scaled_input_to_actual'])}")
        if "target_to_actual" in e:
            print(f"  cilj   -> stvarno (vjernost izvrsenja) : {_fmt(e['target_to_actual'])}")
        if "command_to_actual" in e:
            print(f"  naredba-> stvarno (servo, NE mimikrija): {_fmt(e['command_to_actual'])}")
        ev = e["safety_events"]
        print(f"  sigurnost: rate-limit {ev.get('ratelim_ticks', 0)}, "
              f"range-clamp {ev.get('rangeclamp_ticks', 0)}, "
              f"hold {ev.get('halted_ticks', 0)} takta")

    print(f"\nSummary -> {summary_path}")
    if not args.no_plot:
        cols, joints = _load(path)
        print(f"Figura  -> {plot(path, cols, joints)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
