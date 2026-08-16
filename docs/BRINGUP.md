# SpectraRover Bring-Up Guide

This guide gets the non-RF robot stack operational before HackRF integration.

## Goal of this stage

The robot should be able to:

1. boot the Jetson software environment
2. communicate with the ESP32 motor controller over USB serial
3. independently command all four mecanum wheels
4. stop automatically if commands are lost
5. use the Logitech C270 (or another OpenCV-visible camera)
6. calibrate the selected camera
7. detect ArUco markers
8. autonomously approach a marker and follow a marker sequence

The HackRF receive pipeline, RF analysis, and RF-driven next-direction decision are intentionally outside this bring-up stage.

## 1. Hardware checks before power

- Verify motor supply voltage.
- Measure or obtain motor stall current before choosing TB6612FNG as the final driver.
- Confirm common ground between ESP32 and motor drivers.
- Keep Jetson power separate from the motor-driver output rail.
- Keep the chassis on blocks for first motor tests.
- Do not connect the unidentified cylindrical sensors directly to 3.3 V GPIO until their exact electrical interface is verified.

## 2. Motor-controller firmware

Flash:

```text
firmware/esp32/esp32_motor_controller.ino
```

The firmware boots DISARMED and includes a 500 ms command watchdog.

Expected boot message:

```text
SPECTRAROVER MOTOR CONTROLLER READY DISARMED
```

## 3. Find the ESP32 serial port

Linux/Jetson examples:

```bash
ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
```

Set the correct value in `config/config.yaml` under `motor_controller.port`.

## 4. Wheel-by-wheel bench test

Dry run first:

```bash
python3 scripts/motor_bench.py
```

Then, with the chassis physically lifted so the wheels cannot drive the robot away:

```bash
python3 scripts/motor_bench.py --arm
```

The test exercises each wheel independently, then forward/reverse, strafing, and rotation.

If an individual wheel spins in the wrong direction, change only that wheel's value under:

```yaml
robot:
  wheel_polarity:
    front_left: 1
    front_right: 1
    rear_left: 1
    rear_right: 1
```

Use `-1` to invert a wheel. Do not rewrite the kinematics to compensate for wiring polarity.

## 5. Find the camera

For the confirmed Logitech C270, start with index 0:

```bash
python3 scripts/list_cameras.py
```

Update `camera.device_index` in `config/config.yaml` if needed.

## 6. Calibrate the camera

Print or display a standard chessboard calibration target. The defaults expect 9 x 6 inner corners with 25 mm squares.

```bash
python3 scripts/calibrate_camera.py --device 0 --cols 9 --rows 6 --square-mm 25
```

Capture at least 8 views; 15-25 varied views is better. The generated file is:

```text
config/camera_calibration.yaml
```

## 7. Generate visual navigation markers

```bash
python3 scripts/generate_aruco_markers.py --ids 0 1 2 3
```

The software uses OpenCV `DICT_4X4_50`. Print the markers at a known physical size and set the measured black-square width in `navigation.aruco.marker_length_m`.

## 8. Camera-guided navigation dry run

Place marker 0 in front of the robot and run:

```bash
python3 scripts/aruco_route.py --markers 0
```

No physical motor output occurs without `--arm`. The serial commands are printed instead.

## 9. First physical visual-navigation test

Use a clear floor area, low motor limit, and one marker first:

```bash
python3 scripts/aruco_route.py --markers 0 --arm
```

The robot stops if the marker is lost longer than the configured timeout. Start with the robot several meters or less from the marker and keep a physical power cutoff within reach.

## 10. Multi-marker route

After the single-marker behavior is verified:

```bash
python3 scripts/aruco_route.py --markers 0 1 2 3 --arm
```

This gives the project a complete pre-HackRF autonomous movement stack using the existing camera and mecanum base.

## What still requires physical validation

Software can be complete before hardware integration, but these items cannot be truthfully marked verified until measured on the actual robot:

- exact wheel polarity
- correct ESP32 pin wiring to the chosen motor drivers
- motor-driver current margin
- selected camera index and calibration
- marker physical size
- stable low-speed PWM value for the real chassis
- effect of floor friction and mecanum roller orientation

These are calibration/bring-up values, not missing software modules.
