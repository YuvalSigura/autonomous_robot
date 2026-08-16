#!/usr/bin/env python3
from __future__ import annotations

import argparse
import time
from pathlib import Path

import yaml

from src.navigation.aruco_follow import ArucoFollowConfig, ArucoFollower
from src.robot.mecanum import mix_mecanum
from src.robot.serial_link import MotorControllerLink, MotorLinkConfig
from src.vision.aruco_localization import ArucoLocalizer, load_calibration
from src.vision.camera import CameraConfig, OpenCVCamera


def load_yaml(path: str) -> dict:
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Drive SpectraRover through a sequence of visible ArUco markers."
    )
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--calibration", default="config/camera_calibration.yaml")
    parser.add_argument("--markers", nargs="+", type=int, required=True)
    parser.add_argument("--arm", action="store_true", help="Enable physical motor output")
    parser.add_argument("--lost-timeout", type=float, default=0.40)
    parser.add_argument("--settle-frames", type=int, default=5)
    args = parser.parse_args()

    cfg = load_yaml(args.config)
    cam_cfg = cfg["camera"]
    camera = CameraConfig(
        device_index=int(cam_cfg["device_index"]),
        width=int(cam_cfg["resolution"]["width"]),
        height=int(cam_cfg["resolution"]["height"]),
        fps=int(cam_cfg["frame_rate"]),
    )

    calibration = load_calibration(args.calibration)
    aruco_cfg = cfg["navigation"]["aruco"]
    localizer = ArucoLocalizer(
        calibration=calibration,
        marker_length_m=float(aruco_cfg["marker_length_m"]),
    )
    follower = ArucoFollower(
        ArucoFollowConfig(
            target_distance_m=float(aruco_cfg["target_distance_m"]),
            distance_tolerance_m=float(aruco_cfg["distance_tolerance_m"]),
            lateral_tolerance_m=float(aruco_cfg["lateral_tolerance_m"]),
            forward_gain=float(aruco_cfg["forward_gain"]),
            lateral_gain=float(aruco_cfg["lateral_gain"]),
            yaw_gain=float(aruco_cfg["yaw_gain"]),
            max_forward=float(aruco_cfg["max_forward"]),
            max_lateral=float(aruco_cfg["max_lateral"]),
            max_yaw=float(aruco_cfg["max_yaw"]),
        )
    )

    mc = cfg["motor_controller"]
    robot = cfg["robot"]
    link_cfg = MotorLinkConfig(
        port=str(mc["port"]),
        baudrate=int(mc["baudrate"]),
        command_limit=float(robot["max_command"]),
    )

    print("Route:", " -> ".join(str(x) for x in args.markers))
    print("Motor output:", "ARMED" if args.arm else "DRY-RUN")

    with OpenCVCamera(camera) as cam, MotorControllerLink(link_cfg, dry_run=not args.arm) as link:
        link.arm()
        try:
            for target_id in args.markers:
                print(f"Seeking marker {target_id}")
                last_seen = time.monotonic()
                reached_frames = 0

                while True:
                    frame = cam.read()
                    observations = localizer.detect(frame)
                    target = next((o for o in observations if o.marker_id == target_id), None)

                    if target is None:
                        if time.monotonic() - last_seen > args.lost_timeout:
                            link.stop()
                        time.sleep(0.02)
                        continue

                    last_seen = time.monotonic()
                    cmd = follower.command(target)
                    if cmd.reached:
                        reached_frames += 1
                        link.stop()
                        if reached_frames >= args.settle_frames:
                            print(f"Reached marker {target_id}")
                            break
                    else:
                        reached_frames = 0
                        wheels = mix_mecanum(
                            cmd.vx,
                            cmd.vy,
                            cmd.wz,
                            limit=float(robot["max_command"]),
                        )
                        link.send_wheels(wheels)

                    time.sleep(0.02)
        except KeyboardInterrupt:
            print("Interrupted; stopping.")
        finally:
            link.stop()
            link.disarm()


if __name__ == "__main__":
    main()
