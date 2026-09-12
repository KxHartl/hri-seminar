"""Automatska analiza okluzije markera iz telemetrijskog zapisa pokusa T-10 (T3c).

Skripta pronalazi tocan pocetak, kraj i trajanje okluzije po zglobovima,
te identificira koji su zglobovi bili zamrznuti (nadlaktica/podlaktica),
a koji su nastavili raditi (saka/zapesce).
"""

from __future__ import annotations
import csv
from pathlib import Path
import numpy as np

REPO_ROOT = Path(r"d:\truenas_kresimir_share_cp\FSB\semestar_09\hri-seminar")
RESULTS_DIR = REPO_ROOT / "data/raw/lab_session_01092026_020000/telemetry"


def detect_occlusion_window(track_csv_path: Path, joint: str = "J1") -> dict:
    """Detektira tocan vremenski prozor zamrzavanja signala uslijed okluzije."""
    with open(track_csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    t = np.array([float(r["t_s"]) for r in rows])
    cmd = np.array([float(r[f"cmd_{joint}_deg"]) for r in rows])

    diffs = np.abs(np.diff(cmd))
    zero_diff = diffs < 1e-4

    max_len = 0
    best_start_idx = 0
    best_end_idx = 0

    cur_len = 0
    cur_start = 0
    for i, zd in enumerate(zero_diff):
        if zd:
            if cur_len == 0:
                cur_start = i
            cur_len += 1
            if cur_len > max_len:
                max_len = cur_len
                best_start_idx = cur_start
                best_end_idx = i + 1
        else:
            cur_len = 0

    t_start = float(t[best_start_idx])
    t_end = float(t[best_end_idx])
    duration = t_end - t_start
    frozen_val = float(cmd[best_start_idx])

    mask = (t >= t_start) & (t <= t_end)
    joint_activity = {}
    for k in range(1, 7):
        cmd_k = np.array([float(r[f"cmd_J{k}_deg"]) for r in rows])[mask]
        std_cmd = float(np.std(cmd_k))
        joint_activity[f"J{k}"] = {
            "frozen": std_cmd < 0.05,
            "std_deg": std_cmd,
            "range_deg": float(np.ptp(cmd_k))
        }

    return {
        "t_start_s": t_start,
        "t_end_s": t_end,
        "duration_s": duration,
        "frozen_val_deg": frozen_val,
        "ticks": max_len,
        "joint_activity": joint_activity
    }


def main():
    csv_p = RESULTS_DIR / "T-10.track.csv"
    if not csv_p.exists():
        print(f"Datoteka {csv_p} ne postoji!")
        return

    res = detect_occlusion_window(csv_p, joint="J1")
    print("=" * 60)
    print("REZULTATI AUTOMATSKE DETEKCIJE OKLUZIJE (T-10 / T3c)")
    print("=" * 60)
    print(f"Pocetak okluzije:  t = {res['t_start_s']:.3f} s")
    print(f"Kraj okluzije:     t = {res['t_end_s']:.3f} s")
    print(f"Trajanje okluzije: Delta t = {res['duration_s']:.3f} s ({res['ticks']} taktova)")
    print(f"Zadrzana vrijednost J1: {res['frozen_val_deg']:.2f} deg")
    print("-" * 60)
    print("Status zglobova tijekom okluzije:")
    for j, act in res["joint_activity"].items():
        status = "ZAMRZNUT (drzi proslu pozu)" if act["frozen"] else f"AKTIVAN (raspon {act['range_deg']:.2f} deg)"
        print(f"  {j}: {status}")
    print("=" * 60)


if __name__ == "__main__":
    main()
