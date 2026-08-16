from __future__ import annotations

import argparse
import math
import time
from pathlib import Path

import yaml

from src.navigation.active_rf_search import ActiveRFSearchPlanner
from src.navigation.waypoint import Pose2D
from src.rf.simulated import SimulatedBeacon
from src.robot.mecanum import mix_mecanum
from src.robot.serial_link import MotorControllerLink, MotorLinkConfig


def load_config(path: str) -> dict:
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_rf_simulation(cfg: dict, iterations: int = 20) -> None:
    rf_cfg = cfg["rf"]
    sim_cfg = rf_cfg["simulated_beacon"]
    search_cfg = rf_cfg["search"]

    beacon = SimulatedBeacon(
        x_m=float(sim_cfg["x_m"]),
        y_m=float(sim_cfg["y_m"]),
        tx_power_db=float(sim_cfg["tx_power_db"]),
        path_loss_exponent=float(sim_cfg["path_loss_exponent"]),
        noise_std_db=float(sim_cfg["noise_std_db"]),
    )
    planner = ActiveRFSearchPlanner(
        step_m=float(search_cfg["step_m"]),
        exploration_weight=float(search_cfg["exploration_weight"]),
    )

    pose = Pose2D(0.0, 0.0, 0.0)
    target = (float(sim_cfg["x_m"]), float(sim_cfg["y_m"]))
    print(f"Simulated source location (hidden from planner): {target}")

    for i in range(iterations):
        obs = beacon.measure(pose)
        planner.add(obs)
        error = math.hypot(pose.x - target[0], pose.y - target[1])
        print(
            f"step={i:02d} pose=({pose.x:.2f},{pose.y:.2f}) "
            f"strength={obs.strength_db:.2f} dB source_error={error:.2f} m"
        )
        if error <= float(search_cfg["stop_radius_m"]):
            print("Source region reached in simulation.")
            break
        decision = planner.choose_next(pose.x, pose.y)
        pose = Pose2D(decision.x, decision.y, pose.yaw)


def run_motor_smoke(cfg: dict, arm: bool) -> None:
    """Low-level bench test. Put the robot on stands before using --arm."""
    mc = cfg["motor_controller"]
    robot_cfg = cfg["robot"]
    link_cfg = MotorLinkConfig(
        port=str(mc["port"]),
        baudrate=int(mc["baudrate"]),
        command_limit=float(robot_cfg["max_command"]),
    )

    dry_run = not arm
    with MotorControllerLink(link_cfg, dry_run=dry_run) as link:
        link.arm()
        patterns = [
            ("forward", mix_mecanum(0.15, 0.0, 0.0, robot_cfg["max_command"])),
            ("strafe-right", mix_mecanum(0.0, 0.15, 0.0, robot_cfg["max_command"])),
            ("rotate", mix_mecanum(0.0, 0.0, 0.15, robot_cfg["max_command"])),
        ]
        for name, command in patterns:
            print(f"motor test: {name} -> {command}")
            link.send_wheels(command)
            time.sleep(0.35 if arm else 0.05)
            link.stop()
            time.sleep(0.25 if arm else 0.05)
        link.disarm()


def main() -> None:
    parser = argparse.ArgumentParser(description="SpectraRover control and research entry point")
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--mode", choices=["rf-sim", "motor-smoke"], default="rf-sim")
    parser.add_argument(
        "--arm",
        action="store_true",
        help="Allow physical motor output in motor-smoke mode. Keep robot on stands for first test.",
    )
    parser.add_argument("--iterations", type=int, default=20)
    args = parser.parse_args()

    cfg = load_config(args.config)
    if args.mode == "rf-sim":
        run_rf_simulation(cfg, args.iterations)
    elif args.mode == "motor-smoke":
        run_motor_smoke(cfg, arm=args.arm)


if __name__ == "__main__":
    main()
