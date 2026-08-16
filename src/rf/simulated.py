from __future__ import annotations

import math
import random
import time

from src.navigation.waypoint import Pose2D
from src.rf.base import RFObservation


class SimulatedBeacon:
    """Simple log-distance beacon model for development without SDR hardware."""

    def __init__(
        self,
        x_m: float,
        y_m: float,
        tx_power_db: float = -20.0,
        path_loss_exponent: float = 2.0,
        noise_std_db: float = 1.5,
        frequency_hz: float = 433_920_000.0,
        seed: int = 7,
    ) -> None:
        self.x_m = x_m
        self.y_m = y_m
        self.tx_power_db = tx_power_db
        self.path_loss_exponent = path_loss_exponent
        self.noise_std_db = noise_std_db
        self.frequency_hz = frequency_hz
        self._rng = random.Random(seed)

    def measure(self, pose: Pose2D) -> RFObservation:
        distance = max(math.hypot(pose.x - self.x_m, pose.y - self.y_m), 0.10)
        path_loss_db = 10.0 * self.path_loss_exponent * math.log10(distance)
        noise = self._rng.gauss(0.0, self.noise_std_db)
        strength = self.tx_power_db - path_loss_db + noise
        return RFObservation(
            x=pose.x,
            y=pose.y,
            strength_db=strength,
            frequency_hz=self.frequency_hz,
            timestamp_s=time.time(),
        )
