"""Live OptiTrack (Motive/NatNet) marker source.

Same :class:`MarkerSource` interface as ``ReplaySource``/``MockMarkerSource``, so
the pipeline is unchanged. Resolves our hand-marker names (``zapesce`` etc.) to
NatNet model-def markers by case-insensitive substring match (robust to Motive's
``MarkerSet 001:zapesce`` style prefixes, mirroring the CSV parser), then streams
positions converted to millimetres.

Decode logic is unit-tested; the live socket path is verified in the lab.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator

import numpy as np

from .base import MarkerFrame, MarkerSource
from .natnet.client import NatNetClient

log = logging.getLogger(__name__)

# Markers required to build the hand frame / flexion angle (palac optional).
REQUIRED = ("zapesce", "srednji", "mali")


def resolve_marker_indices(
    model_def: list[tuple[str, list[str]]],
    targets: dict[str, str],
) -> dict[str, tuple[str, int]]:
    """Map our marker names -> (marker_set_name, index_within_set).

    ``targets`` maps our-name -> Motive substring to look for. Matching is
    case-insensitive substring (handles ``MarkerSet 001:zapesce``).
    """
    resolved: dict[str, tuple[str, int]] = {}
    for our_name, needle in targets.items():
        for set_name, marker_names in model_def:
            for idx, mname in enumerate(marker_names):
                if needle.lower() in mname.lower():
                    resolved[our_name] = (set_name, idx)
                    break
            if our_name in resolved:
                break
    missing = [m for m in REQUIRED if m not in resolved]
    if missing:
        raise ValueError(
            f"NatNet model nema markere {missing}; dostupno: "
            f"{[(s, n) for s, n in model_def]}")
    return resolved


class LiveNatNetSource(MarkerSource):
    def __init__(
        self,
        server_ip: str,
        client_ip: str = "0.0.0.0",
        use_multicast: bool = True,
        marker_name_map: dict[str, str] | None = None,
    ) -> None:
        self.client = NatNetClient(server_ip, client_ip, use_multicast)
        # our-name -> Motive substring (defaults: identity on our four names)
        self.targets = marker_name_map or {m: m for m in ("zapesce", "srednji",
                                                           "mali", "palac")}

    def __iter__(self) -> Iterator[MarkerFrame]:
        self.client.connect()
        model_def = self.client.request_model_def()
        resolved = resolve_marker_indices(model_def, self.targets)
        log.info("NatNet markeri razriješeni: %s", resolved)

        seq = 0
        for _frame_no, marker_sets in self.client.frames():
            by_set = {name: pts for name, pts in marker_sets}
            markers: dict[str, np.ndarray] = {}
            ok = True
            for our_name, (set_name, idx) in resolved.items():
                pts = by_set.get(set_name)
                if pts is None or idx >= len(pts):
                    if our_name in REQUIRED:
                        ok = False
                        break
                    continue
                markers[our_name] = pts[idx] * 1000.0  # m -> mm
            if not ok:
                continue  # occlusion / missing required marker -> drop; fail-safe covers it
            yield MarkerFrame(seq=seq, t_capture=time.time(), markers=markers)
            seq += 1

    def close(self) -> None:
        self.client.close()
