# SpectraRover

SpectraRover is an autonomous mobile research robot built around an NVIDIA Jetson Orin Nano and a four-wheel mecanum base. The physical platform already exists; the current project branch prepares the complete **pre-HackRF** stack: motor control, fail-safe communications, camera support, calibration, visual navigation, autonomous movement, documentation, and tests.

![SpectraRover hardware overview](docs/assets/spectrarover-hardware-overview.webp)

> Development branch: `spectrarover-rebuild`
>
> The non-RF software stack is implemented and CI-tested. Hardware-specific values such as final wheel polarity, serial device name, camera intrinsics, motor-driver current margin, and sensor electrical interfaces remain chassis-specific calibration/verification items.

## Project goal

The next research stage adds HackRF Pro as a new sensing modality. Instead of only navigating through the physical environment, the rover will be able to collect RF observations at different positions and use those observations to drive RF-aware experiments such as spatial measurement, source-seeking, anomaly analysis, and active selection of the next measurement location.

The intended loop is:

```text
MOVE
  -> STOP MOTORS
  -> SETTLE
  -> CAPTURE RF
  -> ANALYZE
  -> CHOOSE NEXT TARGET
  -> MOVE
```

The RF acquisition, RF/AI analysis, and final RF-evidence-to-next-waypoint policy are intentionally **not claimed as complete** before HackRF integration.

## Current hardware

Current/available hardware documented from the existing platform and component inventory includes:

- NVIDIA Jetson Orin Nano Developer Kit 8 GB
- four-wheel mecanum / omni-directional chassis
- 4 x geared DC motors
- ESP32 development board with screw-terminal expansion board
- L298N motor-driver hardware currently available/installed
- 2 x TB6612FNG dual H-bridge breakout boards available for independent four-motor control, subject to stall-current verification
- Logitech C270 camera (one confirmed camera option; the vision layer is camera-agnostic)
- small I2C OLED display
- front-mounted cylindrical proximity/photoelectric sensors, exact electrical interface to be verified
- HC-SR04 ultrasonic modules available
- u-blox NEO-6M GPS + antenna available for outdoor logging
- Seeed Studio XIAO RP2040 available as an auxiliary MCU
- Arduino Uno-compatible boards for bench/prototyping work
- 3-cell 18650 battery pack / power system
- breadboards, jumper leads, resistors, LEDs, switches, and prototyping power modules

See [`docs/HARDWARE.md`](docs/HARDWARE.md), [`docs/WIRING.md`](docs/WIRING.md), and [`docs/BRINGUP.md`](docs/BRINGUP.md).

## System architecture

```text
                       +---------------------------+
                       |      Jetson Orin Nano     |
                       |---------------------------|
 Camera -------------->| vision / localization    |
 Future HackRF Pro --->| RF DSP / ML / planner    |
                       | waypoint / mission logic  |
                       +-------------+-------------+
                                     |
                                USB serial
                                     |
                       +-------------v-------------+
                       |            ESP32          |
                       |---------------------------|
                       | explicit ARM / DISARM     |
                       | command watchdog          |
                       | four-wheel motor output   |
                       +-------------+-------------+
                                     |
                            motor-driver stage
                                     |
                            FL  FR  RL  RR motors
```

The Jetson does not directly drive the motors. It sends bounded wheel commands to the ESP32. The ESP32 owns the low-level outputs and stops/disarms if commands disappear.

## Implemented pre-HackRF software

### Motor and chassis

- four-wheel mecanum inverse kinematics: `vx`, `vy`, `wz` -> FL / FR / RL / RR
- forward, reverse, lateral strafe, diagonal motion, and rotation command patterns
- per-wheel polarity configuration
- Jetson-to-ESP32 serial motor protocol
- explicit ARM / DISARM state
- firmware communications watchdog
- bounded motor output
- individual-wheel and full-chassis bench utility
- dry-run mode that cannot physically move the rover

### Vision and navigation

- generic OpenCV camera wrapper
- camera discovery utility
- camera calibration utility
- ArUco marker generation
- calibrated ArUco pose estimation
- marker approach/follow controller
- autonomous route through a sequence of visual markers
- generic 2D pose-to-waypoint controller that can later accept another localization backend
- stop behavior when the visual navigation target is lost

### Engineering / validation

- deterministic unit tests for mecanum kinematics, navigation behavior, and serial safety state
- GitHub Actions CI
- startup self-check for camera + ESP32 communications
- hardware inventory, wiring notes, and staged bring-up procedure

## Quick bring-up

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the non-moving startup checks:

```bash
python3 scripts/startup_check.py
```

Find available cameras:

```bash
python3 scripts/list_cameras.py
```

Calibrate the selected navigation camera:

```bash
python3 scripts/calibrate_camera.py --device 0 --cols 9 --rows 6 --square-mm 25
```

Generate navigation markers:

```bash
python3 scripts/generate_aruco_markers.py --ids 0 1 2 3
```

Preview the complete motor test without physical movement:

```bash
python3 scripts/motor_bench.py
```

First physical motor test should be performed with the chassis safely lifted so all wheels are off the floor:

```bash
python3 scripts/motor_bench.py --arm
```

Camera-guided route, dry-run:

```bash
python3 scripts/aruco_route.py --markers 0 1 2
```

Camera-guided route with motor output enabled after bring-up/calibration:

```bash
python3 scripts/aruco_route.py --markers 0 1 2 --arm
```

## Safety defaults

- ESP32 boots DISARMED
- physical motor output requires an explicit arm action
- command magnitude is capped
- communications timeout stops and disarms the drive controller
- visual-navigation target loss causes a stop after a short timeout
- motor bring-up is simulation/dry-run first

## HackRF phase

The future HackRF Pro integration is deliberately separated behind the RF interface so the rest of the rover does not need to be redesigned. Planned work includes:

1. receive-side HackRF integration and reproducible IQ/spectral observations
2. spatial RF measurements associated with rover pose
3. controlled source-seeking experiments using an owned/authorized beacon
4. signal/event feature extraction and anomaly/clustering experiments
5. uncertainty-aware selection of the next measurement location
6. characterization of self-generated EMI from motors, PWM, USB, power conversion, and onboard computing

A simple simulated RF source remains as a development boundary for testing interfaces; it is not presented as the final HackRF implementation.

## ROS 2 compatibility direction

The core code is intentionally lightweight and does **not** require ROS 2 today. The interfaces map naturally onto ROS 2 concepts, however: body velocity commands can map to `Twist`, wheel control can be wrapped by `ros2_control`, pose/odometry can be published through standard messages, and the existing waypoint target can later be supplied by Nav2 or another planner.

Keeping this optional means the current rover can run directly on the Jetson while leaving a clean path to a full ROS 2 navigation stack if the project grows into SLAM, sensor fusion, or larger multi-node experiments.

## Repository layout

```text
config/                 runtime and calibration configuration
firmware/esp32/         low-level four-motor controller
src/robot/              serial motor link + mecanum kinematics
src/navigation/         waypoint + visual navigation controllers
src/vision/             camera + ArUco pose estimation
src/rf/                 future RF interface / simulation boundary
scripts/                 hardware bring-up and navigation utilities
docs/                    hardware, wiring, bring-up, and assets
tests/                   deterministic non-hardware tests
.github/workflows/       CI tests
```

## Pre-HackRF status

- [x] physical mecanum robot platform exists
- [x] Jetson-based onboard compute platform exists
- [x] ESP32 fail-safe four-motor firmware
- [x] mecanum kinematics + configurable wheel polarity
- [x] serial motor-control layer
- [x] motor bring-up utility
- [x] generic camera layer
- [x] camera calibration utility
- [x] visual marker localization / approach controller
- [x] multi-marker autonomous route code
- [x] startup self-check
- [x] unit tests + CI
- [x] hardware and wiring documentation
- [x] README hardware overview illustration
- [ ] chassis-specific electrical and calibration verification
- [ ] HackRF Pro receive integration
- [ ] RF/AI analysis pipeline
- [ ] RF evidence -> next-waypoint policy
- [ ] controlled RF source-seeking experiments

## License

MIT. See [`LICENSE`](LICENSE).
