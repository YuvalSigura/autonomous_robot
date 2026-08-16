# SpectraRover

SpectraRover is an open-source autonomous mobile research robot built around a Jetson Orin Nano. The current platform combines mecanum-wheel mobility, onboard compute, proximity sensing, computer vision, and a modular control stack. The next research stage is to add software-defined radio sensing with HackRF Pro so the robot can perform RF-aware navigation, spatial RF measurements, source-seeking experiments, and AI-assisted anomaly analysis.

> Status: active rebuild on the `spectrarover-rebuild` branch. The robot hardware already exists. RF hardware integration is planned; the software includes a simulated RF source so the navigation and source-seeking logic can be developed before SDR hardware is available.

## Current hardware

Verified from the existing robot/repository and recent build photos:

- NVIDIA Jetson Orin Nano Developer Kit 8 GB as the high-level computer
- 4-wheel mecanum chassis
- 4 DC geared TT-style motors
- ESP32 development board with screw-terminal I/O expansion board
- L298N motor-driver hardware currently available/installed
- two TB6612FNG dual H-bridge breakout boards available as a more efficient four-motor driver option (subject to motor stall-current verification)
- USB camera / vision input planned around the existing Logitech C270 configuration
- small I2C OLED display
- multiple cylindrical proximity/photoelectric sensors mounted around the chassis (exact model/electrical interface must be verified before final wiring)
- HC-SR04 ultrasonic sensor modules available
- IR receiver module available
- u-blox NEO-6M GPS module + antenna available for outdoor logging (not intended as the primary indoor localization source)
- Seeed Studio XIAO RP2040 available as an auxiliary sensor/safety microcontroller
- Arduino Uno-compatible boards available for bench tests
- breadboards, jumper leads, resistors, LEDs, switches and prototyping power modules

## Recommended system architecture

```text
                      +-------------------------+
                      |      Jetson Orin Nano   |
                      |-------------------------|
 Camera / pose ------>| vision + localization  |
 HackRF Pro (future)->| RF DSP / ML / planner  |
                      | waypoint controller     |
                      +------------+------------+
                                   |
                              USB serial
                                   |
                      +------------v------------+
                      |          ESP32          |
                      |-------------------------|
                      | watchdog / E-stop       |
                      | 4-wheel motor control   |
                      +------------+------------+
                                   |
                         2 x TB6612FNG
                                   |
                          FL FR RL RR motors
```

The Jetson is deliberately kept out of direct motor-driving duty. It sends bounded velocity/wheel commands to a dedicated microcontroller. The ESP32 owns the motor outputs and enforces a communications watchdog, so loss of the Jetson process or USB link stops the robot.

## Why replace the L298N stage?

For a mecanum platform, independent control of all four wheels is desirable. Two TB6612FNG boards provide four H-bridge channels with substantially lower losses than the classic L298N topology. They should only be used after measuring each motor's stall current and confirming that the driver ratings are appropriate. The repository therefore treats motor-driver selection as a hardware validation item rather than assuming compatibility.

## Software already included on this branch

- mecanum inverse kinematics (`vx`, `vy`, `wz` -> four wheel commands)
- bounded serial motor protocol
- ESP32 motor-controller firmware with explicit ARM/DISARM and communications watchdog
- waypoint controller for pose-to-target motion
- active RF source-seeking baseline that can run against a simulated beacon
- RF observation interface ready for a future HackRF-backed implementation
- dry-run/simulation-first main program
- configuration for motor limits, serial link and RF simulation

## Safety defaults

The software is intentionally fail-safe:

- physical motors are **not armed by default**
- the ESP32 requires an explicit `ARM` command
- a dead-man timeout stops all motors if commands stop arriving
- speed is capped in configuration
- use blocks/stands for first wheel tests so the chassis cannot run away

## RF research direction

The HackRF Pro stage is intended to turn the existing robot into an RF-aware mobile research platform. Planned experiments include:

1. spatial RF measurement while the robot moves between known poses
2. autonomous source-seeking for an authorized/owned beacon
3. anomaly detection and clustering of RF observations
4. active sensing: selecting the next waypoint that is expected to reduce source-location uncertainty
5. characterization of self-generated EMI from motors, PWM, DC/DC conversion and onboard computing

A key measurement mode will be **move -> stop -> settle -> capture RF -> analyze -> move**, which reduces contamination from the robot's own motors during RF collection.

## Repository layout

```text
config/                 runtime configuration
firmware/esp32/         low-level four-motor controller
src/robot/              motor link + mecanum kinematics
src/navigation/         waypoint and RF-search planning
src/rf/                 RF interfaces + simulator
src/main.py              simulation / hardware entry point
docs/                    hardware, wiring and architecture notes
tests/                   deterministic unit tests
```

## Near-term milestones

- [x] physical mecanum robot platform
- [x] Jetson-based compute platform
- [x] repository and containerized development environment
- [x] safe four-wheel control architecture
- [x] simulated RF source-seeking baseline
- [ ] verify exact motor stall current
- [ ] wire 2 x TB6612FNG or select higher-current drivers if required
- [ ] verify mounted proximity sensor model and output voltage
- [ ] add repeatable indoor pose source (wheel encoders + IMU, or camera/ArUco reference localization)
- [ ] bench-test physical movement at low speed
- [ ] integrate HackRF Pro receive pipeline
- [ ] run controlled authorized-beacon localization experiments

## License

MIT. See `LICENSE`.
