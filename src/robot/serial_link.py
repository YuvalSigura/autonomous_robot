from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import serial

from .mecanum import WheelCommand


@dataclass
class MotorLinkConfig:
    port: str = "/dev/ttyUSB0"
    baudrate: int = 115200
    command_limit: float = 0.35


class MotorControllerLink:
    """Small, explicit protocol to the ESP32 motor controller.

    Physical motion requires both an explicit `arm()` call and firmware-side ARM state.
    """

    def __init__(self, config: MotorLinkConfig, dry_run: bool = True) -> None:
        self.config = config
        self.dry_run = dry_run
        self._serial: Optional[serial.Serial] = None
        self._armed = False

    def open(self) -> None:
        if self.dry_run:
            return
        self._serial = serial.Serial(
            self.config.port,
            self.config.baudrate,
            timeout=0.2,
            write_timeout=0.2,
        )
        time.sleep(1.0)
        self.stop()

    def close(self) -> None:
        try:
            self.disarm()
        finally:
            if self._serial is not None:
                self._serial.close()
                self._serial = None

    def _write(self, line: str) -> None:
        if self.dry_run:
            print(f"[DRY-RUN motor] {line}")
            return
        if self._serial is None:
            raise RuntimeError("Motor link is not open")
        self._serial.write((line.rstrip() + "\n").encode("ascii"))
        self._serial.flush()

    def arm(self) -> None:
        self._write("ARM")
        self._armed = True

    def disarm(self) -> None:
        if self._armed or self.dry_run:
            self._write("DISARM")
        self._armed = False

    def stop(self) -> None:
        self._write("STOP")

    def send_wheels(self, command: WheelCommand) -> None:
        if not self._armed:
            raise RuntimeError("Refusing motor command: controller is not armed")
        command = command.clipped(self.config.command_limit)
        self._write(
            "WHEELS "
            f"{command.front_left:.4f} {command.front_right:.4f} "
            f"{command.rear_left:.4f} {command.rear_right:.4f}"
        )

    def __enter__(self) -> "MotorControllerLink":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
