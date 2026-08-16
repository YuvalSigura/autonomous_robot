from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

# Allow both `python -m src.main` and `python src/main.py` from the repo root.
if __package__ in (None, ""):
    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

import yaml

from src.navigation.active_rf_search import ActiveRFSearchPlanner
from src.navigation.waypoint import Pose2D
from src.rf.simulated import SimulatedBeacon
from src.robot.mecanum import WheelCommand, mix_mecanum
from src.robot.serial_link import MotorControllerLink, MotorLinkConfig


def load_config(path: str) -> dict:
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _apply_polarity(command: WheelCommand, robot_cfg: dict) -> WheelCommand:
    polarity = robot_cfg.get("wheel_polarity", {})
    return command.with_polarity(
        int(polarity.get("front_left", 1)),
        int(polarity.get("front_right", 1)),
        int(polarity.get("rear_left", 1)),
        int(polarity.get("rear_right", 1)),
    )


def run_rf_simulation(cfg: dict, iterations: int = 20) -> None:
    """Exercise the future RF/planner interface with a synthetic beacon only."""
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
    """Short low-level bench test; use `scripts/motor_bench.py` for full bring-up."""
    mc = cfg["motor_controller"]
    robot_cfg = cfg["robot"]
    link_cfg = MotorLinkConfig(
        port=str(mc["port"]),
        baudrate=int(mc["baudrate"]),
        command_limit=float(robot_cfg["max_command"]),
    )

    with MotorControllerLink(link_cfg, dry_run=not arm) as link:
        link.arm()
        try:
            patterns = [
                ("forward", mix_mecanum(0.15, 0.0, 0.0, 1.0)),
                ("strafe-right", mix_mecanum(0.0, 0.15, 0.0, 1.0)),
                ("rotate", mix_mecanum(0.0, 0.0, 0.15, 1.0)),
            ]
            for name, raw_command in patterns:
                command = _apply_polarity(raw_command, robot_cfg)
                print(f"motor test: {name} -> {command}")
                link.send_wheels(command)
                time.sleep(0.35 if arm else 0.05)
                link.stop()
                time.sleep(0.25 if arm else 0.05)
        finally:
            link.stop()
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
    else:
        run_motor_smoke(cfg, arm=args.arm)


if __name__ == "__main__":
    main()
