# SpectraRover Hardware Notes

This document separates **verified components**, **likely components that still need electrical verification**, and **recommended additions** before physical autonomous tests.

## Verified / clearly identified from the build and component photos

### Compute
- NVIDIA Jetson Orin Nano Developer Kit 8 GB (high-level compute)
- ESP32 DevKit-style microcontroller on a screw-terminal expansion board
- Seeed Studio XIAO RP2040 available as an auxiliary MCU
- Arduino Uno-compatible boards available for bench/prototyping work

### Mobility
- 4-wheel mecanum chassis
- 4 x yellow TT-style geared DC motors
- L298N H-bridge module(s) available/currently used
- 2 x TB6612FNG dual H-bridge breakout boards available

### Position / sensing / UI
- multiple cameras are available for the project; the original repository mentioned a Logitech C270, but the vision code is now camera-agnostic and accepts any OpenCV-visible USB/CSI camera
- HC-SR04 ultrasonic modules available
- IR receiver module available
- u-blox NEO-6M GPS receiver + external antenna available
- small I2C OLED display mounted on the compute enclosure
- breadboards, resistors, jumper wires, LEDs, buttons and prototyping power modules

## Camera plan

Because several cameras are available, the first RF source-seeking demo does not need a new camera purchase.

Recommended use:

1. **Primary navigation/localization camera**
   - choose the camera with the most stable Linux/OpenCV support, wide enough field of view and reliable exposure
   - calibrate it once and use ArUco/AprilTag reference markers for repeatable indoor position during early experiments

2. **Optional secondary camera**
   - forward-facing obstacle/scene camera, recording camera, or later stereo experiment
   - not required for the first autonomous RF experiment

Using two cameras for stereo is possible, but it adds synchronization and calibration complexity. For the first reproducible demonstration, one calibrated camera plus known visual reference markers is the lower-risk design.

## Components visible but exact model/electrical interface must be confirmed

The cylindrical yellow/orange chassis sensors appear to be E18-D80NK-style photoelectric/IR proximity sensors or a similar family. Do **not** wire them to Jetson/ESP32 inputs based only on appearance. Confirm the exact part number, supply range and output type first.

An ACEBOTT packaged sensor is also visible, but the exact sensor model is not legible enough to document safely from the photograph alone.

## Motor-driver recommendation

For mecanum motion, four motors should be independently controlled.

Preferred first test configuration:
- TB6612FNG #1 -> front-left + front-right
- TB6612FNG #2 -> rear-left + rear-right
- shared STBY line
- one PWM + two direction signals per motor

Why: the TB6612FNG is a modern MOSFET H-bridge and is generally much more efficient than the L298N bipolar driver topology.

**Do not assume it can handle these motors.** Measure or obtain the motor stall current first. If the stall current is above the safe capability of the TB6612FNG, use a higher-current four-channel motor-driver solution instead.

## Navigation hardware gap

The current chassis can support basic commanded movement and proximity-based obstacle avoidance, but robust autonomous navigation needs a repeatable pose estimate.

Best options, in order of effort:

1. **Camera + ArUco/AprilTag reference localization**
   - uses one of the cameras already available
   - ideal for controlled indoor demonstrations
   - no wheel hardware change required
   - initial code is included under `src/vision/`

2. **Wheel encoders + IMU**
   - better general-purpose odometry
   - requires encoders or motors with encoders
   - recommended long-term

3. **2D lidar or depth camera**
   - useful for SLAM and obstacle mapping
   - not required for the first RF source-seeking demonstration

GPS (NEO-6M) is useful for outdoor logging but is not the primary solution for indoor source-seeking.

## Recommended additional parts to look for in your component collection

If available, these are especially useful:

- IMU: BNO085/BNO055, ICM-20948, MPU-6050/9250, or similar
- wheel encoders / magnetic encoder modules
- emergency-stop button or latching power switch
- buck/boost regulator sized for the robot computer power rail
- motor suppression capacitors / ferrites
- current sensor such as INA219/INA226 for power diagnostics
- directional antenna for later RF source-seeking experiments

A new camera is **not** currently a priority because multiple cameras are already available.

## RF integration design notes

The robot itself is an RF-noisy environment. Major interference sources include:
- DC motor commutation
- PWM motor drive
- DC/DC converters
- Jetson compute electronics
- USB links
- display and sensor wiring

The first HackRF integration should therefore place the SDR antenna away from the motor/power electronics and use a measurement cycle such as:

```text
MOVE -> STOP MOTORS -> WAIT FOR EMI TO SETTLE -> CAPTURE RF -> ANALYZE -> MOVE
```

The software configuration already includes a `settle_before_rf_s` parameter for this purpose.
