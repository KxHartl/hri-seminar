"""Hardened parser for OptiTrack (Motive) marker-export CSV files.

Replaces the brittle exercise parser (``load_optitrack_data``) with explicit,
validated parsing. The Motive export has a 7-row header; the marker-name row and
the data rows share the same column alignment (empty/``Frame`` col at index 0,
``Time`` at 1, first marker X at 2), so a marker's name-row column index is used
directly as its data-column index — no offset. See ``data/raw/reference_mocap/README.md``
for the full format contract.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np

EXPECTED_MARKERS = ("zapesce", "palac", "srednji", "mali")
# vjezbe_01 uses "dlan" instead of "zapesce"; callers may pass a custom set.
N_COORDS = 3


@dataclass(frozen=True)
class OptiTrackTake:
    """Parsed OptiTrack take.

    Attributes:
        markers: mapping marker-name -> array (n_frames, 3) of XYZ in millimetres.
        time_s: array (n_frames,) capture time in seconds.
        frame_rate_hz: nominal capture frame rate from the file metadata.
        take_name: take name from the file metadata.
        path: source file path.
    """

    markers: dict[str, np.ndarray]
    time_s: np.ndarray
    frame_rate_hz: float
    take_name: str
    path: Path

    @property
    def n_frames(self) -> int:
        return int(self.time_s.shape[0])


def _parse_metadata_row(row: list[str]) -> dict[str, str]:
    """Row 1 is a flat key,value,key,value,... list."""
    return {row[i].strip(): row[i + 1].strip()
            for i in range(0, len(row) - 1, 2) if row[i].strip()}


def load_take(
    path: str | Path,
    marker_names: tuple[str, ...] = EXPECTED_MARKERS,
) -> OptiTrackTake:
    """Load and validate a Motive marker-export CSV.

    Args:
        path: CSV file path.
        marker_names: marker substrings to extract (case-insensitive).

    Returns:
        An :class:`OptiTrackTake`.

    Raises:
        ValueError: on malformed header, missing markers, NaN values, or a
            frame-count mismatch against the file metadata.
    """
    path = Path(path)
    with path.open("r", newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.reader(fh))

    if len(rows) < 8:
        raise ValueError(f"{path.name}: premalo redaka ({len(rows)}), očekivano >= 8")

    meta = _parse_metadata_row(rows[0])
    take_name = meta.get("Take Name", path.stem)
    frame_rate = float(meta.get("Capture Frame Rate", "120") or "120")
    total_frames_meta = int(meta.get("Total Frames in Take", "0") or "0")
    units = meta.get("Length Units", "Millimeters")
    if units.lower() not in ("millimeters", "millimetres", "mm"):
        raise ValueError(f"{path.name}: očekivane jedinice mm, dobiveno '{units}'")

    name_row = rows[3]          # ",Name,<set>:<marker>,..."
    data_rows = rows[7:]        # numeric data starts at row index 7 (8th line)

    # Map each marker to the column index of its first (X) component.
    col_of: dict[str, int] = {}
    for marker in marker_names:
        idxs = [i for i, cell in enumerate(name_row)
                if marker.lower() in cell.strip().lower()]
        if len(idxs) < N_COORDS:
            raise ValueError(
                f"{path.name}: marker '{marker}' ima {len(idxs)} stupaca, "
                f"očekivano >= {N_COORDS}")
        col_of[marker] = idxs[0]

    # Parse numeric data into a (n_frames, n_cols) array, tolerating blank lines.
    data_rows = [r for r in data_rows if r and r[0].strip() != ""]
    n_frames = len(data_rows)
    max_col = max(col_of.values()) + N_COORDS
    arr = np.full((n_frames, max_col), np.nan, dtype=float)
    for i, r in enumerate(data_rows):
        ncol = min(len(r), max_col)
        for j in range(ncol):
            cell = r[j].strip()
            if cell:
                arr[i, j] = float(cell)

    time_s = arr[:, 1].copy()

    markers: dict[str, np.ndarray] = {}
    for marker, c in col_of.items():
        xyz = arr[:, c:c + N_COORDS]
        if np.isnan(xyz).any():
            raise ValueError(f"{path.name}: marker '{marker}' sadrži NaN/prazne vrijednosti")
        markers[marker] = xyz

    if total_frames_meta and total_frames_meta != n_frames:
        raise ValueError(
            f"{path.name}: broj okvira {n_frames} != metapodatak "
            f"'Total Frames in Take' {total_frames_meta}")

    return OptiTrackTake(
        markers=markers,
        time_s=time_s,
        frame_rate_hz=frame_rate,
        take_name=take_name,
        path=path,
    )
