"""Real-time pipeline: OptiTrack replay -> UDP -> angle -> filter -> safety -> UR.

Assembles every stage from ``src/config/default.yaml``. The marker stream is
produced by a sender thread (replay -> UDP) and consumed by a background
receiver; the control loop runs at the robot's control rate, pulling the latest
frame, computing the hand-flexion angle, filtering it, passing it through the
safety guard, and issuing a single-joint ``servoJ`` command.

Run:
    python -m src.pipeline.main --config src/config/default.yaml --seconds 20
    python -m src.pipeline.main --sink dry_run --seconds 5      # no robot needed
"""

from __future__ import annotations

import argparse
import itertools
import json
import logging
import sys
import threading
import time
from pathlib import Path

import yaml

# UTF-8 stdout on Windows consoles.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

from src.filtering.factory import make_filter
from src.kinematics.hand_frame import hand_frame_single
from src.kinematics.joint_angle import flexion_angle
from src.optitrack.replay_source import ReplaySource, TrackReplaySource, send_over_udp
from src.pipeline.delay import DelayLine
from src.pipeline.latency import LatencyLog
from src.pipeline.tracklog import JointSample, TrackLog
from src.receiver import BackgroundReceiver
from src.robot import make_sink
from src.safety.guard import SafetyGuard

log = logging.getLogger("pipeline")
REPO_ROOT = Path(__file__).resolve().parents[2]


import contextlib
import ctypes


@contextlib.contextmanager
def high_resolution_timer():
    """Raise the Windows timer resolution to 1 ms so time.sleep is accurate.

    Without this, the default ~15.6 ms scheduler tick caps the replay sender well
    below 120 Hz. No-op on non-Windows platforms.
    """
    is_win = sys.platform == "win32"
    if is_win:
        ctypes.windll.winmm.timeBeginPeriod(1)
    try:
        yield
    finally:
        if is_win:
            ctypes.windll.winmm.timeEndPeriod(1)


def load_config(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _start_sender(cfg: dict, host: str, port: int) -> threading.Thread:
    src = cfg["source"]
    if src.get("track"):
        track_path = REPO_ROOT / src["track"]
        source = TrackReplaySource(track_path, loop=src.get("loop", False))
    else:
        take_path = REPO_ROOT / src["take"]
        source = ReplaySource(
            take_path, marker_names=tuple(src["marker_names"]),
            loop=src.get("loop", True),
        )

    def _run() -> None:
        send_over_udp(source, host, port, drop_rate=src.get("drop_rate", 0.0))

    th = threading.Thread(target=_run, name="sender", daemon=True)
    th.start()
    return th


def _single_joint_loop(cfg, sink, rx, lat, n_steps, dt, fs, home_joint, j,
                       track=None, delay=None, estop_after=None) -> None:
    """Single-DOF control: one hand-flexion angle drives one joint (original path)."""
    kin, mp, saf, rob = cfg["kinematics"], cfg["mapping"], cfg["safety"], cfg["robot"]
    filt = make_filter(cfg["filter"], fs_hz=fs)
    guard = SafetyGuard(
        home=home_joint,
        max_joint_speed_dps=saf["max_joint_speed_dps"],
        joint_range_dps=saf["joint_range_dps"],
        signal_timeout_s=saf["signal_timeout_s"],
    )
    gain = float(mp.get("gain", 1.0))
    invert = -1.0 if mp.get("invert", False) else 1.0
    offset = float(mp.get("offset_from_home_rad", 0.0))
    wname, mname, pname = kin["wrist_marker"], kin["middle_marker"], kin["pinky_marker"]
    R_ref = None
    prev_R = None
    step_desc = f"{n_steps} koraka" if (n_steps is not None and n_steps > 0) else "kontinuirano (Ctrl-C za kraj)"
    log.info("Start: %s @ %.0f Hz, zglob J%d, sink=%s",
             step_desc, fs, j + 1, rob["sink"])

    t_run0 = time.time()
    estop_done = False
    step_iter = range(n_steps) if (n_steps is not None and n_steps > 0) else itertools.count()
    for _ in step_iter:
        t_start = sink.init_period()
        if estop_after is not None and not estop_done and time.time() - t_run0 >= estop_after:
            guard.trip_estop()
            estop_done = True
            log.warning("SOFTVERSKI E-STOP okinut na t=%.2f s — izlaz zamrznut.",
                        time.time() - t_run0)
        frame, age = rx.get_latest()
        if delay is not None:
            frame, age = delay.push_and_get(time.time(), frame, age)

        target = home_joint
        raw = filtered = 0.0
        t_capture = time.time()
        if frame is not None and wname in frame.markers:
            t_capture = frame.t_capture
            R, _ok = hand_frame_single(
                frame.markers[wname], frame.markers[mname],
                frame.markers[pname], prev_R)
            prev_R = R
            if R_ref is None:
                R_ref = R
            raw = flexion_angle(R, R_ref)             # pre-filter human angle
            filtered = filt(raw, t_capture)           # causal real-time filter
            target = home_joint + offset + gain * invert * filtered

        decision = guard.step(target, dt, signal_age_s=age)
        sink.servo_joint(j, decision.angle)
        lat.record(t_capture, time.time(), age if age != float("inf") else 0.0)
        if track is not None:
            actual = sink.get_actual_q() if (track.log_actual and track.due) else None
            track.record(
                time.time() - t_run0, t_capture,
                {j: JointSample(raw, filtered, target, decision.angle,
                                decision.rate_limited, decision.range_clamped,
                                decision.halted)},
                actual)
        sink.wait_period(t_start)


def _multi_joint_loop(cfg, sink, rx, lat, n_steps, dt, fs, home_q,
                      track=None, delay=None, estop_after=None) -> None:
    """6-DOF control: the bridge's 6 channel angles drive all six joints (mimicry).

    The bridge sends each channel as a named scalar 'marker' (x = angle [rad]). Each
    joint gets its own causal filter and :class:`SafetyGuard`. Channels are re-zeroed
    at the first received frame so the robot starts from its own home regardless of
    when the bridge homed.
    """
    saf, rob = cfg["safety"], cfg["robot"]
    mapping = cfg["arm_mapping"]
    timeout_s = saf["signal_timeout_s"]

    filt = {m["channel"]: make_filter(cfg["filter"], fs_hz=fs) for m in mapping}
    guards = {}
    for m in mapping:
        jj = int(m["joint"])
        guards[jj] = SafetyGuard(
            home=home_q[jj],
            max_joint_speed_dps=float(m.get("max_speed_dps", saf["max_joint_speed_dps"])),
            joint_range_dps=float(m.get("range_dps", saf["joint_range_dps"])),
            signal_timeout_s=timeout_s,
        )
    home_ch: dict[str, float] = {}
    joints = sorted({int(m["joint"]) for m in mapping})
    names = ["base", "shoulder", "elbow", "wrist_1", "wrist_2", "wrist_3"]
    step_desc = f"{n_steps} koraka" if (n_steps is not None and n_steps > 0) else "kontinuirano (Ctrl-C za kraj)"
    log.info("Start: %s @ %.0f Hz, multi_joint zglobovi=%s, sink=%s",
             step_desc, fs, [jjj + 1 for jjj in joints], rob["sink"])
    log_every = max(1, int(fs))               # ~1 s

    t_run0 = time.time()
    estop_done = False
    step_iter = range(n_steps) if (n_steps is not None and n_steps > 0) else itertools.count()
    for step in step_iter:
        t_start = sink.init_period()
        if estop_after is not None and not estop_done and time.time() - t_run0 >= estop_after:
            for g in guards.values():
                g.trip_estop()
            estop_done = True
            log.warning("SOFTVERSKI E-STOP okinut na t=%.2f s — izlaz zamrznut.",
                        time.time() - t_run0)
        frame, age = rx.get_latest()
        if delay is not None:
            frame, age = delay.push_and_get(time.time(), frame, age)
        t_capture = frame.t_capture if frame is not None else time.time()

        if frame is not None and not home_ch:        # re-home channels at first frame
            home_ch = {m["channel"]: float(frame.markers[m["channel"]][0])
                       for m in mapping if m["channel"] in frame.markers}

        q = list(home_q)
        samples = {}
        for m in mapping:
            jj = int(m["joint"])
            ch = m["channel"]
            guard = guards[jj]
            raw = val = 0.0
            if frame is not None and ch in frame.markers:
                gain = float(m.get("gain", 1.0))
                invert = -1.0 if m.get("invert", False) else 1.0
                offset = float(m.get("offset_rad", 0.0))
                raw = float(frame.markers[ch][0]) - home_ch.get(ch, 0.0)
                val = filt[ch](raw, t_capture)
                target = home_q[jj] + offset + gain * invert * val
            else:
                target = guard.last                   # no data -> hold last
            decision = guard.step(target, dt, signal_age_s=age)
            q[jj] = decision.angle
            if track is not None:
                samples[jj] = JointSample(
                    raw, val, target, decision.angle, decision.rate_limited,
                    decision.range_clamped, decision.halted)

        sink.servo_q(q)
        lat.record(t_capture, time.time(), age if age != float("inf") else 0.0)
        if track is not None:
            actual = sink.get_actual_q() if (track.log_actual and track.due) else None
            track.record(time.time() - t_run0, t_capture, samples, actual)
        if step % log_every == 0:
            deltas = "  ".join(
                f"{names[jj]}={(q[jj] - home_q[jj]) * 57.2958:+5.1f}" for jj in joints)
            log.info("t=%4.1fs  Δzglob[deg]: %s%s", step / fs, deltas,
                     "  [HOLD]" if age > saf["signal_timeout_s"] else "")
        sink.wait_period(t_start)


def run(cfg: dict, seconds: float | None = None) -> dict:
    udp, kin, mp = cfg["udp"], cfg["kinematics"], cfg["mapping"]
    saf, rob = cfg["safety"], cfg["robot"]

    # Connect the robot FIRST (RTDE connect takes ~2 s); only then start the
    # marker stream, so no frames go stale during connect (avoids a startup
    # latency outlier).
    sink = make_sink(rob["sink"], rob["ip"], control_hz=rob["control_hz"],
                     lookahead_time=rob.get("servoj", {}).get("lookahead_time", 0.1),
                     gain=rob.get("servoj", {}).get("gain", 300))
    sink.connect()
    home_q = sink.get_home_q()
    j = int(mp["joint_index"])
    home_joint = home_q[j]

    # Bind the receiver (port may be 0 = OS-assigned). Start the internal replay
    # sender ONLY for in-process replay; for a live OptiTrack stream (or an
    # external replay_sender process) the markers come from outside, exactly as
    # in the lab — main only receives.
    rx = BackgroundReceiver(udp["host"], udp["port"]).start()
    src_kind = cfg["source"].get("kind", "replay")
    internal = src_kind == "replay" and cfg["source"].get("in_process", True)
    if internal:
        _start_sender(cfg, udp["host"], rx.port)
        wait_s = 1.0
    else:
        log.info("Čekam vanjski izvor markera na %s:%d (kind=%s) ...",
                 udp["host"], udp["port"], src_kind)
        wait_s = 10.0
    _t0 = time.perf_counter()
    while rx.get_latest()[0] is None and time.perf_counter() - _t0 < wait_s:
        time.sleep(0.005)
    if rx.get_latest()[0] is None:
        log.warning("Nije primljen nijedan marker-frame; pokrećem uz fail-safe (hold).")

    fs = float(rob["control_hz"])
    lat = LatencyLog()
    dt = 1.0 / fs
    n_steps = int(seconds * fs) if (seconds is not None and seconds > 0) else None
    ctrl = cfg.get("control", {})
    mode = ctrl.get("mode", "single_joint")
    logcfg = cfg.get("logging", {})

    # Angle logging (input vs command vs actual) -- off unless a path is given,
    # so existing runs and tests are unaffected.
    track = None
    track_csv = logcfg.get("track_csv")
    if track_csv:
        if mode == "multi_joint":
            track_joints = tuple(sorted({int(m["joint"]) for m in cfg["arm_mapping"]}))
        else:
            track_joints = (j,)
        track = TrackLog(
            joints=track_joints,
            home_q=tuple(home_q),
            log_actual=bool(logcfg.get("log_actual", False)),
            decimate=int(logcfg.get("track_decimate", 1)),
        )

    estop_after = ctrl.get("estop_after_s")
    estop_after = float(estop_after) if estop_after else None

    added_ms = float(ctrl.get("added_latency_ms", 0.0) or 0.0)
    delay = DelayLine(added_ms / 1e3) if added_ms > 0 else None
    if delay is not None:
        log.warning("Umjetna latencija +%.0f ms (signal_timeout_s=%.2f s) — "
                    "timeout mora biti veći od dodane latencije.",
                    added_ms, saf["signal_timeout_s"])

    loop_t0 = time.perf_counter()
    try:
        with high_resolution_timer():
            if mode == "multi_joint":
                _multi_joint_loop(cfg, sink, rx, lat, n_steps, dt, fs, home_q,
                                  track=track, delay=delay, estop_after=estop_after)
            else:
                _single_joint_loop(cfg, sink, rx, lat, n_steps, dt, fs, home_joint, j,
                                   track=track, delay=delay, estop_after=estop_after)
    except KeyboardInterrupt:
        log.warning("Prekinuto (Ctrl-C).")
    else:
        if n_steps is not None and n_steps > 0:
            loop_hz = n_steps / max(time.perf_counter() - loop_t0, 1e-9)
            if abs(loop_hz - fs) > 0.1 * fs:
                log.error("TAKT NE ODGOVARA: petlja %.0f Hz, a safety računa s %.0f Hz "
                          "(dt=%.1f ms) — ograničenje brzine je efektivno %.1fx labavije/"
                          "strože. Provjeri control_hz i RTDE frekvenciju.",
                          loop_hz, fs, dt * 1e3, loop_hz / fs)
            else:
                log.info("Takt petlje: %.1f Hz (ciljano %.0f Hz).", loop_hz, fs)
    finally:
        sink.stop()
        sink.disconnect()
        rx.stop()

    stats = rx.stats
    summary = {
        "latency": lat.summary(),
        "rx_rate_hz": round(stats.rate_hz, 1),
        "rx_jitter_ms": round(stats.interarrival_jitter_ms, 2),
        "rx_received": stats.received,
        "rx_lost": stats.lost,
        "rx_loss_pct": round(stats.loss_pct, 2),
        "rx_reordered": stats.reordered,
    }
    if added_ms > 0:
        summary["added_latency_ms"] = added_ms
    if track is not None:
        summary["safety_events"] = track.summary()["joints"]
    out_csv = REPO_ROOT / logcfg.get("latency_csv", "data/processed/latency.csv")
    lat.to_csv(out_csv)
    # Per-run metrics summary next to the CSV (handy for the lab results table).
    summary_path = out_csv.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Latencija: %s", summary["latency"])
    log.info("Prijem: rate=%.1fHz jitter=%.2fms primljeno=%d izgubljeno=%d (%.2f%%) reorder=%d",
             stats.rate_hz, stats.interarrival_jitter_ms, stats.received,
             stats.lost, stats.loss_pct, stats.reordered)
    log.info("Latency CSV -> %s  | summary -> %s", out_csv, summary_path)
    if track is not None:
        track_path = REPO_ROOT / track_csv
        track.to_csv(track_path)
        log.info("Track CSV -> %s (%d redaka, zglobovi=%s, actual=%s)",
                 track_path, len(track.rows),
                 [jj + 1 for jj in track.joints], track.log_actual)
    return summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Real-time OptiTrack -> UR pipeline")
    ap.add_argument("--config", default=str(REPO_ROOT / "src/config/default.yaml"))
    ap.add_argument("--seconds", type=float, default=20.0)
    ap.add_argument("--mode", default=None,
                    help="override control.mode (single_joint|multi_joint)")
    ap.add_argument("--sink", default=None, help="override robot.sink (ursim|ur3e|dry_run)")
    ap.add_argument("--ip", default=None, help="override robot.ip (npr. 192.168.40.50)")
    ap.add_argument("--joint", type=int, default=None,
                    help="override mapping.joint_index (0-based; 3=wrist_1, 4=wrist_2)")
    ap.add_argument("--range-dps", type=float, default=None,
                    help="override safety.joint_range_dps (± otklon oko home [deg])")
    ap.add_argument("--max-speed-dps", type=float, default=None,
                    help="override safety.max_joint_speed_dps ([deg/s])")
    ap.add_argument("--gain", type=float, default=None,
                    help="override mapping.gain (ljudski kut -> robot kut, single_joint)")
    ap.add_argument("--invert", action="store_true",
                    help="override mapping.invert (obrni smjer gibanja, single_joint)")
    ap.add_argument("--filter", default=None, help="override filter.kind")
    ap.add_argument("--drop-rate", type=float, default=None,
                    help="override source.drop_rate (samo za interni sender; "
                         "uz --external zadaj ga mostu live_sender)")
    ap.add_argument("--port", type=int, default=None, help="override udp.port")
    ap.add_argument("--external", action="store_true",
                    help="ne pokreći interni sender; očekuj vanjski izvor (Motive/replay_sender)")
    ap.add_argument("--latency-csv", default=None,
                    help="putanja za latency CSV ovog runa (npr. data/raw/lab_session_01092026_020000/telemetry/run01.csv)")
    ap.add_argument("--track-csv", default=None,
                    help="putanja za CSV s kutovima (ulaz/filtar/naredba[/stvarno]) po zglobu; "
                         "bez ovog flaga se kutovi ne logiraju")
    ap.add_argument("--log-actual", action="store_true",
                    help="uz --track-csv logiraj i STVARNI kut robota (RTDE getActualQ)")
    ap.add_argument("--track-decimate", type=int, default=None,
                    help="zapiši svaki N-ti takt u track CSV (dugi endurance runovi)")
    ap.add_argument("--added-latency-ms", type=float, default=None,
                    help="umjetno kašnjenje ulaza [ms] prije sigurnosnog sloja; "
                         "PODIGNI safety.signal_timeout_s iznad ove vrijednosti")
    ap.add_argument("--estop-after", type=float, default=None,
                    help="okini SOFTVERSKI e-stop nakon N sekundi (dokazni test; "
                         "izlaz se zamrzava i to se vidi u track CSV-u kao halted)")
    ap.add_argument("--signal-timeout-s", type=float, default=None,
                    help="override safety.signal_timeout_s (npr. 0.6 za sweep latencije)")
    ap.add_argument("--replay-track", default=None,
                    help="replay a 6-DOF .track.csv file in-process over UDP")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    if args.mode:
        cfg.setdefault("control", {})["mode"] = args.mode
    if args.sink:
        cfg["robot"]["sink"] = args.sink
    if args.ip:
        cfg["robot"]["ip"] = args.ip
    if args.joint is not None:
        cfg["mapping"]["joint_index"] = args.joint
    if args.range_dps is not None:
        cfg["safety"]["joint_range_dps"] = args.range_dps
        for m in cfg.get("arm_mapping", []):   # cap EVERY joint (multi_joint safety ceiling)
            m["range_dps"] = min(float(m.get("range_dps", args.range_dps)), args.range_dps)
    if args.max_speed_dps is not None:
        cfg["safety"]["max_joint_speed_dps"] = args.max_speed_dps
        for m in cfg.get("arm_mapping", []):
            m["max_speed_dps"] = min(float(m.get("max_speed_dps", args.max_speed_dps)),
                                     args.max_speed_dps)
    if args.gain is not None:
        cfg["mapping"]["gain"] = args.gain
    if args.invert:
        cfg["mapping"]["invert"] = True
    if args.filter:
        cfg["filter"]["kind"] = args.filter
    if args.drop_rate is not None:
        cfg["source"]["drop_rate"] = args.drop_rate
        # source.drop_rate is only read by _start_sender, which never runs with
        # --external. Passing it here dropped nothing during the September lab
        # session and the runs looked complete, so say so loudly instead.
        if args.external:
            log.warning("--drop-rate %.2f NEMA UCINKA uz --external: pakete odasilje "
                        "most, ne pipeline. Zadaj ga mostu: "
                        "live_sender --drop-rate %.2f", args.drop_rate, args.drop_rate)
    if args.port is not None:
        cfg["udp"]["port"] = args.port
    if args.external:
        cfg["source"]["in_process"] = False
    if args.replay_track:
        cfg.setdefault("source", {})["track"] = args.replay_track
        cfg["source"]["kind"] = "replay"
        cfg["source"]["in_process"] = True
        cfg["source"]["loop"] = False
    if args.latency_csv:
        cfg.setdefault("logging", {})["latency_csv"] = args.latency_csv
    if args.track_csv:
        cfg.setdefault("logging", {})["track_csv"] = args.track_csv
    if args.log_actual:
        cfg.setdefault("logging", {})["log_actual"] = True
    if args.track_decimate is not None:
        cfg.setdefault("logging", {})["track_decimate"] = args.track_decimate
    if args.added_latency_ms is not None:
        cfg.setdefault("control", {})["added_latency_ms"] = args.added_latency_ms
    if args.estop_after is not None:
        cfg.setdefault("control", {})["estop_after_s"] = args.estop_after
    if args.signal_timeout_s is not None:
        cfg["safety"]["signal_timeout_s"] = args.signal_timeout_s

    logging.basicConfig(
        level=getattr(logging, cfg.get("logging", {}).get("level", "INFO")),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    run(cfg, args.seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
