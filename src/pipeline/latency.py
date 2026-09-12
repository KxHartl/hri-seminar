"""Per-stage timing instrumentation for end-to-end latency and jitter.

Each control step records the capture timestamp and the wall-clock time at which
the command was issued; the difference is the end-to-end latency. Results are
summarised (median / p95 / jitter) and can be exported to CSV for the report.
"""

from __future__ import annotations

import csv
import statistics
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LatencyLog:
    """Collects (t_capture, t_command, signal_age) samples per control step."""

    rows: list[tuple[float, float, float]] = field(default_factory=list)

    def record(self, t_capture: float, t_command: float, signal_age: float) -> None:
        self.rows.append((t_capture, t_command, signal_age))

    @property
    def latencies_ms(self) -> list[float]:
        return [(tc - tcap) * 1e3 for tcap, tc, _ in self.rows]

    def summary(self) -> dict[str, float]:
        lat = self.latencies_ms
        if not lat:
            return {"n": 0}
        lat_sorted = sorted(lat)

        def _pct(q: float) -> float:            # nearest-rank percentile
            return lat_sorted[min(len(lat_sorted) - 1, int(q * len(lat_sorted)))]

        jitter = statistics.pstdev(lat) if len(lat) > 1 else 0.0
        return {
            "n": len(lat),
            "median_ms": statistics.median(lat),
            "mean_ms": statistics.fmean(lat),
            "p95_ms": _pct(0.95),
            "p99_ms": _pct(0.99),
            "max_ms": max(lat),
            "jitter_ms": jitter,
        }

    def to_csv(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["t_capture", "t_command", "latency_ms", "signal_age_ms"])
            for tcap, tc, age in self.rows:
                w.writerow([f"{tcap:.6f}", f"{tc:.6f}",
                            f"{(tc - tcap) * 1e3:.3f}", f"{age * 1e3:.3f}"])
