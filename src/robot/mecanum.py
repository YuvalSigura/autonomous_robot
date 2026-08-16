from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WheelCommand:
    front_left: float
    front_right: float
    rear_left: float
    rear_right: float

    def clipped(self, limit: float = 1.0) -> "WheelCommand":
        limit = abs(limit)
        values = [self.front_left, self.front_right, self.rear_left, self.rear_right]
        peak = max(max(abs(v) for v in values), 1.0)
        scale = limit / peak if peak > limit else 1.0
        return WheelCommand(*(max(-limit, min(limit, v * scale)) for v in values))


def mix_mecanum(vx: float, vy: float, wz: float, limit: float = 1.0) -> WheelCommand:
    """Convert normalized body velocity into four normalized wheel commands.

    Coordinate convention:
      vx > 0: forward
      vy > 0: strafe right
      wz > 0: rotate clockwise

    Wheel mounting or motor wiring may invert signs on a real chassis; calibrate on stands.
    """
    fl = vx - vy - wz
    fr = vx + vy + wz
    rl = vx + vy - wz
    rr = vx - vy + wz
    return WheelCommand(fl, fr, rl, rr).clipped(limit)
