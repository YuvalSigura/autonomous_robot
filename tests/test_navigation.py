import numpy as np

from src.navigation.aruco_follow import ArucoFollowConfig, ArucoFollower
from src.navigation.waypoint import Pose2D, WaypointController
from src.vision.aruco_localization import MarkerObservation


def obs(x: float, z: float) -> MarkerObservation:
    return MarkerObservation(
        marker_id=1,
        rvec=np.zeros(3, dtype=float),
        tvec=np.array([x, 0.0, z], dtype=float),
    )


def test_waypoint_controller_reaches_close_target():
    controller = WaypointController(tolerance_m=0.12)
    cmd = controller.command(Pose2D(0.0, 0.0, 0.0), 0.05, 0.0)
    assert cmd.reached


def test_aruco_follower_moves_forward_when_far():
    follower = ArucoFollower(ArucoFollowConfig(target_distance_m=0.55))
    cmd = follower.command(obs(0.0, 1.2))
    assert cmd.vx > 0
    assert not cmd.reached


def test_aruco_follower_strafes_toward_right_marker():
    follower = ArucoFollower(ArucoFollowConfig(target_distance_m=0.55))
    cmd = follower.command(obs(0.20, 0.80))
    assert cmd.vy > 0
    assert cmd.wz > 0


def test_aruco_follower_stops_at_target():
    follower = ArucoFollower(ArucoFollowConfig(target_distance_m=0.55))
    cmd = follower.command(obs(0.01, 0.56))
    assert cmd.reached
    assert (cmd.vx, cmd.vy, cmd.wz) == (0.0, 0.0, 0.0)
