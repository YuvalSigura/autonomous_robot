from __future__ import annotations

import math
from dataclasses import dataclass

from src.rf.base import RFObservation


@dataclass(frozen=True)
class SearchDecision:
    x: float
    y: float
    score: float


class ActiveRFSearchPlanner:
    """Baseline next-measurement planner for RF source-seeking.

    This is intentionally a transparent baseline rather than claiming AI.
    It balances predicted signal strength with exploration of poorly sampled space.
    A learned policy can replace this planner later without changing the robot API.
    """

    def __init__(self, step_m: float = 0.5, exploration_weight: float = 0.20) -> None:
        self.step_m = step_m
        self.exploration_weight = exploration_weight
        self.observations: list[RFObservation] = []

    def add(self, observation: RFObservation) -> None:
        self.observations.append(observation)

    def _predict_strength(self, x: float, y: float) -> float:
        if not self.observations:
            return 0.0
        weighted_sum = 0.0
        total_weight = 0.0
        for obs in self.observations:
            d = max(math.hypot(x - obs.x, y - obs.y), 0.05)
            w = 1.0 / (d * d)
            weighted_sum += w * obs.strength_db
            total_weight += w
        return weighted_sum / total_weight

    def _nearest_sample_distance(self, x: float, y: float) -> float:
        if not self.observations:
            return self.step_m
        return min(math.hypot(x - o.x, y - o.y) for o in self.observations)

    def choose_next(self, x: float, y: float) -> SearchDecision:
        candidates = [
            (x + self.step_m, y),
            (x - self.step_m, y),
            (x, y + self.step_m),
            (x, y - self.step_m),
            (x + self.step_m, y + self.step_m),
            (x + self.step_m, y - self.step_m),
            (x - self.step_m, y + self.step_m),
            (x - self.step_m, y - self.step_m),
        ]

        # RF strength is usually negative dB: larger (less negative) is better.
        best = None
        for cx, cy in candidates:
            predicted = self._predict_strength(cx, cy)
            exploration = self._nearest_sample_distance(cx, cy)
            score = predicted + self.exploration_weight * exploration
            decision = SearchDecision(cx, cy, score)
            if best is None or decision.score > best.score:
                best = decision
        assert best is not None
        return best
