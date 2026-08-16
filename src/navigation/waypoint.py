from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, hypot, pi, sin


@dataclass
class Pose2D:
    x: float
    y: float
    yaw: float = 0.0


@dataclass
class VelocityCommand:
    vx: float
    vy: float
    wz: float
    reached: bool = False


def _wrap_angle(a: float) -> float:
    while a > pi:
        a -= 2 * pi
    while a < -pi:
        a += 2 * pi
    return a


class WaypointController:
    """Simple holonomic waypoint controller for a mecanum base."""

    def __init__(
        self,
        tolerance_m: float = 0.12,
        linear_gain: float = 0.8,
        angular_gain: float = 1.2,
        max_linear: float = 0.30,
        max_angular: float = 0.30,
    ) -> None:
        self.tolerance_m = tolerance_m
        self.linear_gain = linear_gain
        self.angular_gain = angular_gain
        self.max_linear = max_linear
        self.max_angular = max_angular

    def command(self, pose: Pose2D, target_x: float, target_y: float) -> VelocityCommand:
        dx = target_x - pose.x
        dy = target_y - pose.y
        distance = hypot(dx, dy)
        if distance <= self.tolerance_m:
            return VelocityCommand(0.0, 0.0, 0.0, reached=True)

        # Convert world-frame error to robot body frame.
        body_x = cos(pose.yaw) * dx + sin(pose.yaw) * dy
        body_y = -sin(pose.yaw) * dx + cos(pose.yaw) * dy

        vx = max(-self.max_linear, min(self.max_linear, self.linear_gain * body_x))
        vy = max(-self.max_linear, min(self.max_linear, self.linear_gain * body_y))

        desired_heading = atan2(dy, dx)
        heading_error = _wrap_angle(desired_heading - pose.yaw)
        wz = max(-self.max_angular, min(self.max_angular, self.angular_gain * heading_error))
        return VelocityCommand(vx, vy, wz, reached=False)
