"""LiveNatNetSource decode logic (no sockets): name resolution + m->mm mapping."""

from __future__ import annotations

import numpy as np
import pytest

from src.optitrack.natnet import protocol as P
from src.optitrack.live_source import resolve_marker_indices


def test_resolve_with_prefixed_names():
    model_def = [("MarkerSet 001", ["MarkerSet 001:mali", "MarkerSet 001:palac",
                                    "MarkerSet 001:srednji", "MarkerSet 001:zapesce"])]
    targets = {"zapesce": "zapesce", "srednji": "srednji", "mali": "mali", "palac": "palac"}
    resolved = resolve_marker_indices(model_def, targets)
    assert resolved["zapesce"] == ("MarkerSet 001", 3)
    assert resolved["mali"] == ("MarkerSet 001", 0)
    assert resolved["srednji"] == ("MarkerSet 001", 2)


def test_resolve_missing_required_raises():
    model_def = [("hand", ["palac", "srednji", "mali"])]  # no zapesce
    with pytest.raises(ValueError):
        resolve_marker_indices(model_def, {"zapesce": "zapesce", "srednji": "srednji",
                                           "mali": "mali"})


def test_full_decode_and_map_to_mm():
    # Build a model def + a frame, then parse and map -> named markers in mm.
    names = ["zapesce", "palac", "srednji", "mali"]
    model_def = P.parse_model_def(P.build_model_def([("MarkerSet 001", names)]))
    pos_m = np.array([[0.10, 1.40, -0.16],   # zapesce (metres)
                      [0.13, 1.36, -0.12],   # palac
                      [0.13, 1.37, -0.04],   # srednji
                      [0.09, 1.38, -0.07]])  # mali
    _, sets = P.parse_frame_marker_sets(
        P.build_frame_marker_sets(7, [("MarkerSet 001", pos_m)]))

    resolved = resolve_marker_indices(model_def, {m: m for m in names})
    by_set = {n: p for n, p in sets}
    got = {our: by_set[s][i] * 1000.0 for our, (s, i) in resolved.items()}

    np.testing.assert_allclose(got["zapesce"], [100.0, 1400.0, -160.0], atol=1e-3)
    np.testing.assert_allclose(got["srednji"], [130.0, 1370.0, -40.0], atol=1e-3)
