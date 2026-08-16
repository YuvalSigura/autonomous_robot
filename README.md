# SpectraRover

SpectraRover is an autonomous mobile research robot built around a Jetson Orin Nano and a four-wheel mecanum base. The physical robot already exists. The current rebuild focuses on making the complete non-RF stack reproducible first: four-wheel motor control, safety/watchdog behavior, camera support, camera calibration, visual navigation, and autonomous movement. HackRF Pro integration is the planned next research stage.

> Current development branch: `spectrarover-rebuild`.
>
> Important status distinction: the software stack below is implemented, but physical values such as wheel polarity, motor-driver current margin, serial port, and camera calibration still have to be measured on the real chassis before they can be called hardware-verified.

## Current hardware

Verified from the existing robot/repository and build photos:

- NVIDIA Jetson Orin Nano Developer Kit 8 GB as the high-level computer
- 4-wheel mecanum chassis
- 4 DC geared TT-style motors
- ESP32 development board with screw-terminal I/O expansion board
- L298N motor-driver hardware currently available/installed
- 2 x TB6612FNG dual H-bridge breakout boards available for independent four-motor control, subject to motor stall-current verification
- multiple camera types available; Logitech C270 is one confirmed model
- small I2C OLED display
- multiple cylindrical proximity/photoelectric sensors mounted around the chassis; exact model/electrical interface still requires verification
- HC-SR04 ultrasonic modules available
- IR receiver module available
- u-blox NEO-6M GPS + antenna available for outdoor logging
- Seeed Studio XIAO RP2040 available as an auxiliary MCU
- Arduino Uno-compatible boards available for bench/prototyping work
- breadboards, jumper leads, resistors, LEDs, switches and prototyping power modules

See `docs/HARDWARE.md` and `docs/WIRING.md` for the component inventory and wiring plan.

## Architecture

```text
                     +--------------------------+
                     |     Jetson Orin Nano     |
                     |--------------------------|
 Camera ------------>| OpenCV / ArUco vision   |
                     | navigation controller    |
 HackRF Pro (future)>| RF DSP / ML / planner   |
                     +------------+-------------+
                                  |
                             USB serial
                                  |
                     +------------v-------------+
                     |          ESP32           |
                     |--------------------------|
                     | ARM / DISARM             |
                     | command watchdog         |
                     | 4 independent motors     |
                     +------------+-------------+
                                  |
                        2 x TB6612FNG
                                  |
                         FL FR RL RR motors
```

The Jetson does not directly drive the motors. It sends bounded wheel commands to the ESP32. The ESP32 owns the H-bridge outputs and stops/disarms on command timeout.

## Implemented non-RF software

### Motor and chassis layer

- four-wheel mecanum inverse kinematics (`vx`, `vy`, `wz` -> FL/FR/RL/RR)
- per-wheel polarity configuration for real-world motor mounting/wiring
- Jetson-to-ESP32 serial motor protocol
- explicit ARM/DISARM states
- firmware watchdog that stops the robot if commands disappear
- individual-wheel and complete-chassis motor bench test
- dry-run mode that cannot move the robot

### Vision and navigation layer

- camera-agnostic OpenCV wrapper
- camera discovery utility
- interactive camera calibration tool
- ArUco marker generation
- ArUco pose estimation using calibrated intrinsics
- visual marker-following controller
- autonomous multi-marker route runner
- generic pose-to-waypoint controller for later global-localization backends

This gives the robot a complete pre-HackRF autonomous movement path that can be validated using only the existing robot and a camera such as the Logitech C270.

## Quick bring-up

Install dependencies:

```bash
pip install -r requirements.txt
```

Find cameras:

```bash
python3 scripts/list_cameras.py
```

Calibrate the selected camera:

```bash
python3 scripts/calibrate_camera.py --device 0 --cols 9 --rows 6 --square-mm 25
```

Generate navigation markers:

```bash
python3 scripts/generate_aruco_markers.py --ids 0 1 2 3
```

Test all four motors without physical movement:

```bash
python3 scripts/motor_bench.py
```

First real motor test must be performed with the chassis on stands:

```bash
python3 scripts/motor_bench.py --arm
```

Camera-guided route, dry-run:

```bash
python3 scripts/aruco_route.py --markers 0 1 2
```

Physical camera-guided route after calibration/bench verification:

```bash
python3 scripts/aruco_route.py --markers 0 1 2 --arm
```

Full instructions are in `docs/BRINGUP.md`.

## Safety defaults

- motor output is disabled unless `--arm` is explicitly supplied
- ESP32 boots DISARMED
- loss of serial commands triggers a watchdog stop/disarm
- motor command magnitude is capped in configuration
- visual-navigation code stops the robot when the target marker is lost beyond a short timeout
- first motor test is designed for a chassis physically lifted off the floor

## What is intentionally not complete yet

The project does **not** claim the HackRF stage is implemented. The following belong to the next research phase:

- HackRF Pro receive integration
- real RF/IQ capture pipeline
- RF event detection / feature extraction / ML analysis
- final algorithm that converts RF evidence/uncertainty into the next movement direction or waypoint
- controlled RF source-seeking experiments

A small simulated RF interface remains in the repository only as a software boundary/prototyping aid; it is not presented as the final RF research result.

## Planned HackRF research

Once HackRF Pro is available, the existing navigation stack can be driven by RF observations instead of visual route targets. Planned experiments include:

1. spatial RF measurements at robot positions
2. autonomous source-seeking for an owned/authorized beacon
3. anomaly detection and clustering of RF observations
4. active sensing: choosing the next measurement location to reduce source-location uncertainty
5. measuring self-generated EMI from motors, PWM, power conversion and onboard computing

A likely RF measurement cycle is:

```text
MOVE -> STOP MOTORS -> SETTLE -> CAPTURE RF -> ANALYZE -> CHOOSE NEXT TARGET -> MOVE
```

## Repository layout

```text
config/                 runtime and calibration configuration
firmware/esp32/         low-level four-motor controller
src/robot/              serial motor link + mecanum kinematics
src/navigation/         waypoint + visual navigation controllers
src/vision/             camera + ArUco pose estimation
src/rf/                 future RF interface / current simulation boundary
scripts/                 hardware bring-up and navigation utilities
docs/                    component inventory, wiring and bring-up notes
tests/                   deterministic non-hardware tests
.github/workflows/       CI test workflow
```

## Pre-HackRF completion checklist

- [x] physical mecanum robot platform exists
- [x] Jetson-based compute platform exists
- [x] ESP32 fail-safe four-motor firmware
- [x] mecanum kinematics and wheel-polarity calibration support
- [x] motor bring-up utility
- [x] generic camera layer
- [x] camera calibration utility
- [x] ArUco detection and approach controller
- [x] multi-marker autonomous route code
- [x] unit tests and CI configuration
- [ ] measure exact motor stall current
- [ ] wire/verify final four-channel motor driver arrangement
- [ ] determine real wheel polarity values on stands
- [ ] calibrate the selected C270/navigation camera on the actual robot
- [ ] validate single-marker physical navigation
- [ ] validate multi-marker physical navigation
- [ ] identify and electrically validate the mounted proximity sensors

## License

MIT. See `LICENSE`.
