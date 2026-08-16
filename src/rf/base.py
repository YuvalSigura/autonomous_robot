from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.navigation.waypoint import Pose2D


@dataclass(frozen=True)
class RFObservation:
    x: float
    y: float
    strength_db: float
    frequency_hz: float | None = None
    timestamp_s: float | None = None


class RFSource(Protocol):
    def measure(self, pose: Pose2D) -> RFObservation:
        ...
