#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import yaml

from src.robot.mecanum import WheelCommand, mix_mecanum
from src.robot.serial_link import MotorControllerLink, MotorLinkConfig


def load_yaml(path: str) -> dict:
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def apply_polarity(command: WheelCommand, robot_cfg: dict) -> WheelCommand:
    p = robot_cfg.get("wheel_polarity", {})
    return command.with_polarity(
        int(p.get("front_left", 1)),
        int(p.get("front_right", 1)),
        int(p.get("rear_left", 1)),
        int(p.get("rear_right", 1)),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="SpectraRover low-speed motor bring-up tool")
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--arm", action="store_true", help="Actually move motors; use chassis stands")
    parser.add_argument("--power", type=float, default=0.16)
    parser.add_argument("--duration", type=float, default=0.35)
    args = parser.parse_args()

    cfg = load_yaml(args.config)
    robot = cfg["robot"]
    mc = cfg["motor_controller"]
    limit = min(abs(args.power), float(robot["max_command"]))

    link_cfg = MotorLinkConfig(
        port=str(mc["port"]),
        baudrate=int(mc["baudrate"]),
        command_limit=float(robot["max_command"]),
    )

    one_wheel = [
        ("front-left", WheelCommand(limit, 0, 0, 0)),
        ("front-right", WheelCommand(0, limit, 0, 0)),
        ("rear-left", WheelCommand(0, 0, limit, 0)),
        ("rear-right", WheelCommand(0, 0, 0, limit)),
    ]
    chassis = [
        ("forward", mix_mecanum(limit, 0, 0, limit=1.0)),
        ("reverse", mix_mecanum(-limit, 0, 0, limit=1.0)),
        ("strafe-right", mix_mecanum(0, limit, 0, limit=1.0)),
        ("strafe-left", mix_mecanum(0, -limit, 0, limit=1.0)),
        ("rotate-clockwise", mix_mecanum(0, 0, limit, limit=1.0)),
        ("rotate-counterclockwise", mix_mecanum(0, 0, -limit, limit=1.0)),
    ]

    print("IMPORTANT: first physical run must be with all wheels off the floor.")
    print("Motor output:", "ARMED" if args.arm else "DRY-RUN")

    with MotorControllerLink(link_cfg, dry_run=not args.arm) as link:
        link.arm()
        try:
            for name, raw in one_wheel + chassis:
                command = apply_polarity(raw, robot)
                print(f"{name:24s} -> {command}")
                link.send_wheels(command)
                time.sleep(args.duration if args.arm else 0.05)
                link.stop()
                time.sleep(0.30 if args.arm else 0.05)
        finally:
            link.stop()
            link.disarm()


if __name__ == "__main__":
    main()
