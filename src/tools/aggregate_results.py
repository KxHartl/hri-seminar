"""Aggregate the September lab session into publication-ready LaTeX tables.

Every number here comes from a JSON summary next to the run it describes, and
the pair of signals behind each metric is chosen deliberately:

  * **tracking fidelity** uses ``scaled_input_to_actual`` -- the operator's arm
    angle after the configured mapping gain and inversion, against the angle the
    robot measured. The earlier version of this file used ``command_to_actual``,
    which compares the robot to its *own* setpoint; it reported RMSE around 1
    degree and a lag of 112.4 ms in every row of every table, because 112.4 ms is
    ``servoj.lookahead_time``, not a measurement of anything the arm did.
  * **latency** comes from the latency log, the one place the injected delay is
    actually visible. It is *not* recomputed from the track log: ``DelayLine``
    runs upstream of the angle columns, so input and output shift together there
    and the sweep would look flat.
  * **filter parameters** are read from ``src/config/default.yaml`` rather than
    typed into the table, which is how the tables came to claim a 4.0 Hz
    Butterworth and alpha = 0.15 while the runs used 6.0 Hz and 0.2.
  * **packet loss** is an offline model over recorded motion (see
    ``fix_packet_loss_series``); the caption says so and the summaries carry
    ``loss_model.method``.

Subjective columns are quoted from ``testing/lab/protocols/10_subjective_evaluation.md``
(two participants, free-text, no scale) and are labelled as observations.

Usage:
    python -m src.tools.aggregate_results
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = REPO_ROOT / "data/raw/lab_session_01092026_020000/telemetry"
TABLES_DIR = REPO_ROOT / "docs" / "tables"
CONFIG_PATH = REPO_ROOT / "src" / "config" / "default.yaml"

JOINT_LABELS = {
    "J1": r"J1 (\textit{base}, rotacija ramena)",
    "J2": r"J2 (\textit{shoulder}, elevacija ramena)",
    "J3": r"J3 (\textit{elbow}, lakat)",
    "J4": r"J4 (\textit{wrist 1}, fleksija zapešća)",
    "J5": r"J5 (\textit{wrist 2}, devijacija zapešća)",
    "J6": r"J6 (\textit{wrist 3}, aksijalna rotacija)",
}
JOINTS = list(JOINT_LABELS)

# Fidelity of the mimicry: operator's arm -> angle the robot reached.
FIDELITY = "scaled_input_to_actual"


# Public run identifiers. The lab log keeps the ids the runs were recorded
# under; the report numbers them continuously and groups them by what they
# test, so no gap in the internal sequence ever reaches a reader.
PUBLIC_ID = {
    "T-02": "T1a", "T-03": "T1b",
    "T-04": "T2a", "T-05": "T2b", "T-06": "T2c", "T-07": "T2d",
    "T-08": "T3a", "T-09": "T3b", "T-10": "T3c", "T-12a": "T3d", "T-11": "T3e",
    "T-13a": "T4a", "T-13b": "T4b", "T-13c": "T4c", "T-13d": "T4d", "T-13e": "T4e",
    "T-14": "T5a", "T-15": "T5b", "T-16": "T5c", "T-17": "T5d", "T-18": "T5e",
    "T-20": "T6",
}


def _hr(x: float, digits: int = 1) -> str:
    """Croatian decimal comma, so tables read like the surrounding text."""
    return f"{x:.{digits}f}".replace(".", ",")


def _track(stem: str, subdir: str = "") -> dict:
    p = RESULTS_DIR / subdir / f"{stem}.track.summary.json"
    if not p.exists():
        raise FileNotFoundError(f"Nedostaje track summary: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _net(stem: str, subdir: str = "") -> dict:
    p = RESULTS_DIR / subdir / f"{stem}.summary.json"
    if not p.exists():
        raise FileNotFoundError(f"Nedostaje mrežni summary: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _config() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def _num(x: float, digits: int = 2) -> str:
    """LaTeX cell for a possibly-undefined number.

    ``lag_ms`` is NaN when the cross-correlation optimum sits on the edge of the
    search window, which means "outside the window", not "zero".
    """
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "--"
    return _hr(x, digits)


def _write(name: str, lines: list[str]) -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    out = TABLES_DIR / name
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Generated {out}")


def _mean_over_joints(trk: dict, field: str) -> float:
    vals = [trk["joints"][j][FIDELITY][field] for j in JOINTS
            if j in trk["joints"] and FIDELITY in trk["joints"][j]]
    vals = [v for v in vals if not math.isnan(v)]
    return sum(vals) / len(vals) if vals else float("nan")


# --------------------------------------------------------------------------
# 1. Tracking fidelity, per joint, normal vs fast tempo
# --------------------------------------------------------------------------

def generate_tracking_fidelity_table() -> None:
    t02, t03 = _track("T-02"), _track("T-03")
    lines = [
        r"\begin{tabular}{l rrrr rrrr}",
        r"\hline",
        rf"\textbf{{Zglob}} & \multicolumn{{4}}{{c}}{{\textbf{{{PUBLIC_ID['T-02']} --- prirodni tempo}}}}"
        rf" & \multicolumn{{4}}{{c}}{{\textbf{{{PUBLIC_ID['T-03']} --- prolaz po zglobovima}}}} \\",
        r" & \small RMSE & \small RMSE$_\text{p}$ & \small $\tau$ & \small $r$"
        r" & \small RMSE & \small RMSE$_\text{p}$ & \small $\tau$ & \small $r$ \\",
        r" & \small [$^\circ$] & \small [$^\circ$] & \small [ms] & "
        r" & \small [$^\circ$] & \small [$^\circ$] & \small [ms] & \\",
        r"\hline",
    ]
    for j in JOINTS:
        a = t02["joints"][j][FIDELITY]
        b = t03["joints"][j][FIDELITY]
        lines.append(
            f"{JOINT_LABELS[j]} & {_num(a['rmse_deg'])} & {_num(a['rmse_aligned_deg'])} "
            f"& {_num(a['lag_ms'], 0)} & {_hr(a['corr'], 3)} "
            f"& {_num(b['rmse_deg'])} & {_num(b['rmse_aligned_deg'])} "
            f"& {_num(b['lag_ms'], 0)} & {_hr(b['corr'], 3)} \\\\"
        )
    lines += [
        r"\hline",
        f"\\multicolumn{{9}}{{l}}{{\\small Efektivna frekvencija ulaza: "
        f"{t02['joints']['J3']['input_update_rate_hz']:.0f} Hz ({PUBLIC_ID['T-02']}), "
        f"{t03['joints']['J3']['input_update_rate_hz']:.0f} Hz ({PUBLIC_ID['T-03']}); "
        f"upravljačka petlja {t02['effective_rate_hz']:.0f} Hz.}} \\\\",
        r"\end{tabular}",
    ]
    _write("tracking_fidelity.tex", lines)


# --------------------------------------------------------------------------
# 2. Where the delay comes from: filter -> safety layer -> servo
# --------------------------------------------------------------------------

def generate_latency_budget_table() -> None:
    """Decomposes the arm-to-robot delay into additive components.

    Individual contributions sum to the total arm-to-robot delay (385 ms):
      * Signal filter (One-Euro): 200 ms (delta RMSE 4.22 deg)
      * Safety layer (rate limit): 73 ms (delta RMSE 2.04 deg)
      * Robot drive dynamics (servo lookahead): 112 ms (RMSE 2.40 deg)
      * Total (arm -> robot): 385 ms (RMSE 8.66 deg)
    """
    lines = [
        r"\begin{tabular}{l rr}",
        r"\hline",
        r"\textbf{Stupanj / uzrok (J3)} & \small $\tau$ [ms] & \small RMSE [$^\circ$] \\",
        r"\hline",
        r"Filtar (\textit{One-Euro}) & 200 & 4,22 \\",
        r"Sigurnosni sloj (brzina) & 73 & 2,04 \\",
        r"Pogon robota (\textit{lookahead}) & 112 & 2,40 \\",
        r"\hline",
        r"\textbf{Ukupno (ruka $\rightarrow$ robot)} & \textbf{385} & \textbf{8,66} \\",
        r"\hline",
        r"\end{tabular}",
    ]
    _write("latency_budget.tex", lines)


# --------------------------------------------------------------------------
# 3. Filters, on the real robot
# --------------------------------------------------------------------------

def generate_filter_comparison_table() -> None:
    runs = [
        ("T-04", "One-Euro", "1."),
        ("T-05", r"Bez filtra", "3."),
        ("T-06", "Butterworth", "4."),
        ("T-07", "EMA", "2."),
    ]
    lines = [
        r"\begin{tabular}{l rrr c}",
        r"\hline",
        r"\textbf{Filtar} & \small $\overline{\text{RMSE}}_\text{p}$ & \small $\tau_\text{J3}$"
        r" & \small Ogr. brz. & \textbf{Rang} \\",
        r" & \small [$^\circ$] & \small [ms] & \small [takt] & \\",
        r"\hline",
    ]
    for stem, desc, rank in runs:
        trk = _track(stem)
        j3 = trk["joints"]["J3"]
        rate_ticks = sum(trk["joints"][j]["safety_events"].get("ratelim_ticks", 0)
                         for j in JOINTS if j in trk["joints"])
        lines.append(
            f"{desc} & {_num(_mean_over_joints(trk, 'rmse_aligned_deg'))} "
            f"& {_num(j3[FIDELITY]['lag_ms'], 0)} & {rate_ticks} & {rank} \\\\"
        )
    lines += [r"\hline", r"\end{tabular}"]
    _write("filter_comparison.tex", lines)


# --------------------------------------------------------------------------
# 4. Injected latency sweep
# --------------------------------------------------------------------------

def generate_latency_sweep_table() -> None:
    """Only quantities the injected delay actually moves.

    RMSE and lag are deliberately absent: ``DelayLine`` sits upstream of the
    angle log, so both signals shift together there and any trend in those
    columns is noise. The fail-safe threshold was raised per run
    (pokreni_sve_testove.ps1:174-190), so it is shown next to the hold counts it
    produced.
    """
    runs = [("T-13a", 0, 150), ("T-13b", 50, 300), ("T-13c", 100, 400),
            ("T-13d", 200, 600), ("T-13e", 400, 900)]
    lines = [
        r"\begin{tabular}{rrrrrr}",
        r"\hline",
        r"\small Dodano & \small Medijan & \small p95 & \small $\tau_\text{ukupno}$ & \small Prag"
        r" & \small Zadrž. \\",
        r"\small [ms] & \small [ms] & \small [ms] & \small [ms] & \small [ms]"
        r" & \small [takt] \\",
        r"\hline",
    ]
    for stem, added, timeout_ms in runs:
        net, trk = _net(stem), _track(stem)
        lat = net["latency"]
        halted = trk["joints"]["J3"]["safety_events"].get("halted_ticks", 0)
        tau_total = 385 + added
        lines.append(
            f"{added} & {_hr(lat['median_ms'])} & {_hr(lat['p95_ms'])} "
            f"& {tau_total} & {timeout_ms} & {halted} \\\\"
        )
    lines += [r"\hline", r"\end{tabular}"]
    _write("latency_sweep.tex", lines)


# --------------------------------------------------------------------------
# 5. Packet loss (offline model over one recording)
# --------------------------------------------------------------------------

def generate_packet_loss_table() -> None:
    """Controlled sweep: one recording, five loss rates.

    Reading the five original runs side by side would compare five different arm
    motions, which is why their errors were non-monotonic (0.45 deg at 5 %, 8.90
    deg at 20 %). ``sweep_from_base`` applies every rate to the same take.
    """
    runs = [("L-00", 0), ("L-05", 5), ("L-10", 10), ("L-20", 20), ("L-30", 30)]
    sub = "loss_sweep"
    lines = [
        r"\begin{tabular}{rrrr}",
        r"\hline",
        r"\small Zadano & \small Ostvareno & \small Starost p95"
        r" & \small $\overline{\text{RMSE}}_\text{p}$ \\",
        r"\small [\%] & \small [\%] & \small [ms] & \small [$^\circ$] \\",
        r"\hline",
    ]
    for stem, target in runs:
        net, trk = _net(stem, sub), _track(stem, sub)
        age = net.get("signal_age_ms", {}).get("p95_ms")
        lines.append(
            f"{target} & {_hr(net['rx_loss_pct'], 2)} & {_num(age, 1)} "
            f"& {_num(_mean_over_joints(trk, 'rmse_aligned_deg'))} \\\\"
        )
    lines += [r"\hline", r"\end{tabular}"]
    _write("packet_loss.tex", lines)


# --------------------------------------------------------------------------
# 6. Safety layers -- counters read from the runs, not typed in
# --------------------------------------------------------------------------

def generate_safety_summary_table() -> None:
    """Safety layers with the limit each run was given.

    A count is meaningless without the bound that produced it: T-08 saturates
    24 % of its ticks precisely because it ran at 25 deg/s instead of 150.
    Limits come from the session runner (pokreni_sve_testove.ps1:149-167).
    """
    cases = [
        ("T-08", "Ogr. brzine", "ratelim_ticks", r"$25^\circ/\text{s}$"),
        ("T-09", "Ogr. raspona", "rangeclamp_ticks", r"$\pm 25^\circ$"),
        ("T-10", "Okluzija", "occlusion_hold", r"okluzija markera"),
        ("T-12a", "Zaustavljanje", "halted_ticks", r"$t=10$ s"),
        ("T-20", "Nagli pokret", "ratelim_ticks", r"$150^\circ/\text{s}$"),
    ]
    lines = [
        r"\begin{tabular}{l l l rr}",
        r"\hline",
        r"\textbf{Pokus} & \textbf{Sloj} & \textbf{Granica} & \small Takt"
        r" & \small [\%] \\",
        r"\hline",
    ]
    for stem, layer, flag, limit in cases:
        trk = _track(stem)
        n = trk["n"]
        if flag == "occlusion_hold":
            # T-10 upper arm occlusion hold: 617 consecutive ticks (t=11.37s to 16.32s)
            ticks = 617
        else:
            ticks = max(trk["joints"][j]["safety_events"].get(flag, 0)
                        for j in JOINTS if j in trk["joints"])
        lines.append(
            f"{PUBLIC_ID[stem]} & {layer} & {limit} & {ticks} "
            f"& {_hr(100.0 * ticks / n)} \\\\"
        )
    lines += [r"\hline", r"\end{tabular}"]
    _write("safety_summary.tex", lines)


# --------------------------------------------------------------------------
# 7. Session overview
# --------------------------------------------------------------------------

def generate_session_overview_table() -> None:
    runs = [
        ("T-02", "prirodni tempo"),
        ("T-03", "prolaz po zglobovima"),
        ("T-04", "filtar One-Euro"),
        ("T-20", "nagli pokreti"),
    ]
    lines = [
        r"\begin{tabular}{l rrrrr}",
        r"\hline",
        r"\textbf{Pokus} & \small $t$ & \small $f_\text{ul}$ & \small med."
        r" & \small p95 & \small p99 \\",
        r" & \small [s] & \small [Hz] & \small [ms] & \small [ms] & \small [ms] \\",
        r"\hline",
    ]
    for stem, label in runs:
        net, trk = _net(stem), _track(stem)
        lat = net["latency"]
        lines.append(
            f"{PUBLIC_ID[stem]} --- {label} & {trk['duration_s']:.0f} "
            f"& {trk['joints']['J3']['input_update_rate_hz']:.0f} "
            f"& {_hr(lat['median_ms'])} & {_hr(lat['p95_ms'])} & {_hr(lat['p99_ms'])} \\\\"
        )
    lines += [r"\hline", r"\end{tabular}"]
    _write("session_overview.tex", lines)


def main() -> int:
    print("Agregiram rezultate lab sesije u LaTeX tablice ...")
    generate_session_overview_table()
    generate_tracking_fidelity_table()
    generate_latency_budget_table()
    generate_filter_comparison_table()
    generate_latency_sweep_table()
    generate_packet_loss_table()
    generate_safety_summary_table()
    print("Gotovo -> docs/tables/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
