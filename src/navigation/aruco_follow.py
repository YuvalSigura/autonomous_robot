from __future__ import annotations

from dataclasses import dataclass
from math import atan2

from src.navigation.waypoint import VelocityCommand
from src.vision.aruco_localization import MarkerObservation


@dataclass(frozen=True)
class ArucoFollowConfig:
    target_distance_m: float = 0.55
    distance_tolerance_m: float = 0.08
    lateral_tolerance_m: float = 0.06
    forward_gain: float = 0.8
    lateral_gain: float = 1.0
    yaw_gain: float = 0.8
    max_forward: float = 0.22
    max_lateral: float = 0.18
    max_yaw: float = 0.20


def _clip(value: float, limit: float) -> float:
    return max(-abs(limit), min(abs(limit), value))


class ArucoFollower:
    """Generate a safe body-frame command that approaches a visible ArUco marker.

    OpenCV solvePnP returns tvec in camera coordinates: +x right, +y down,
    +z forward. This controller assumes a forward-facing camera. If the camera
    is mounted differently, change the mount or add an explicit frame transform.
    """

    def __init__(self, config: ArucoFollowConfig) -> None:
        self.config = config

    def command(self, observation: MarkerObservation) -> VelocityCommand:
        x_right = float(observation.tvec[0])
        z_forward = float(observation.tvec[2])

        forward_error = z_forward - self.config.target_distance_m
        reached = (
            abs(forward_error) <= self.config.distance_tolerance_m
            and abs(x_right) <= self.config.lateral_tolerance_m
        )
        if reached:
            return VelocityCommand(0.0, 0.0, 0.0, reached=True)

        # Mecanum motion lets us correct both range and lateral offset.
        vx = _clip(self.config.forward_gain * forward_error, self.config.max_forward)
        vy = _clip(self.config.lateral_gain * x_right, self.config.max_lateral)

        # Small heading correction keeps the marker close to the camera center.
        bearing = atan2(x_right, max(z_forward, 1e-6))
        wz = _clip(self.config.yaw_gain * bearing, self.config.max_yaw)
        return VelocityCommand(vx, vy, wz, reached=False)
