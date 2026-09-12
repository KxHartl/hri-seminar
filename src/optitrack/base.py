"""Common marker-stream data model and source interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MarkerFrame:
    """One time-step of marker positions.

    Attributes:
        seq: monotonically increasing sequence number (set by the source).
        t_capture: capture timestamp [s] (source clock).
        markers: mapping marker-name -> (3,) XYZ position in millimetres.
    """

    seq: int
    t_capture: float
    markers: dict[str, np.ndarray]


class MarkerSource(ABC):
    """A source of :class:`MarkerFrame` objects (replay file or live stream)."""

    @abstractmethod
    def __iter__(self) -> Iterator[MarkerFrame]:
        ...

    def close(self) -> None:  # optional override
        pass
