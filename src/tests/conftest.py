"""Shared pytest fixtures / paths for the pipeline tests."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data" / "raw" / "reference_mocap"

VJEZBE_02 = DATA_DIR / "vjezbe_02"
VJEZBE_01 = DATA_DIR / "vjezbe_01"

# (path, marker_set) — vjezbe_02 has 'zapesce', vjezbe_01 has 'dlan'.
TAKES_V2 = [
    VJEZBE_02 / "hri_snimanje_vjezbe_02_x.csv",
    VJEZBE_02 / "hri_snimanje_vjezbe_02_y.csv",
    VJEZBE_02 / "hri_snimanje_vjezbe_02_z.csv",
]
TAKE_V1 = VJEZBE_01 / "take_hri_studenti_01.csv"


@pytest.fixture(params=TAKES_V2, ids=lambda p: p.stem)
def take_v2_path(request) -> Path:
    return request.param
