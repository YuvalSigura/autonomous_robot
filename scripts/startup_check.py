#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import yaml

from src.robot.serial_link import MotorControllerLink, MotorLinkConfig
from src.vision.camera import CameraConfig, OpenCVCamera


def load_yaml(path: str) -> dict:
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    parser = argparse.ArgumentParser(description="SpectraRover non-moving startup self-check")
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--skip-motor", action="store_true")
    parser.add_argument("--skip-camera", action="store_true")
    args = parser.parse_args()

    cfg = load_yaml(args.config)
    failures: list[str] = []

    if not args.skip_camera:
        c = cfg["camera"]
        camera_cfg = CameraConfig(
            device_index=int(c["device_index"]),
            width=int(c["resolution"]["width"]),
            height=int(c["resolution"]["height"]),
            fps=int(c["frame_rate"]),
        )
        try:
            with OpenCVCamera(camera_cfg) as camera:
                frame = camera.read()
                h, w = frame.shape[:2]
                print(f"[OK] camera index {camera_cfg.device_index}: {w}x{h}")
        except Exception as exc:
            failures.append(f"camera: {exc}")
            print(f"[FAIL] camera: {exc}")

    calibration = Path("config/camera_calibration.yaml")
    if calibration.exists():
        print(f"[OK] calibration file: {calibration}")
    else:
        print("[INFO] camera calibration not created yet")

    if not args.skip_motor:
        mc = cfg["motor_controller"]
        r = cfg["robot"]
        motor_cfg = MotorLinkConfig(
            port=str(mc["port"]),
            baudrate=int(mc["baudrate"]),
            command_limit=float(r["max_command"]),
        )
        try:
            with MotorControllerLink(motor_cfg, dry_run=False) as link:
                reply = link.ping()
                print(f"[OK] ESP32 motor controller: {reply}")
        except Exception as exc:
            failures.append(f"motor-controller: {exc}")
            print(f"[FAIL] motor-controller: {exc}")

    if failures:
        print("\nStartup check failed:")
        for item in failures:
            print(f"- {item}")
        raise SystemExit(1)

    print("\nAll requested non-moving startup checks passed.")


if __name__ == "__main__":
    main()
