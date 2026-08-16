# Initial Wiring Plan

This is the proposed first-pass wiring for the `spectrarover-rebuild` branch. Verify board labels and motor current before applying power.

## Architecture

- Jetson Orin Nano: high-level navigation / vision / future RF processing
- ESP32: low-level motor controller only
- 2 x TB6612FNG: four independently controlled DC motors
- USB serial: Jetson <-> ESP32 command link

Do not drive motors directly from Jetson GPIO.

## ESP32 -> TB6612FNG pin proposal

The firmware currently uses:

| Wheel | IN1 | IN2 | PWM |
|---|---:|---:|---:|
| Front Left | GPIO 13 | GPIO 14 | GPIO 25 |
| Front Right | GPIO 16 | GPIO 17 | GPIO 26 |
| Rear Left | GPIO 18 | GPIO 19 | GPIO 27 |
| Rear Right | GPIO 21 | GPIO 22 | GPIO 32 |
| Shared STBY | GPIO 33 | - | - |

The two TB6612FNG STBY inputs can be tied together to GPIO 33.

### Driver #1
- Channel A -> front-left motor
- Channel B -> front-right motor

### Driver #2
- Channel A -> rear-left motor
- Channel B -> rear-right motor

If wheel direction is reversed, fix motor polarity or add a software inversion flag after the first stand test. Do not randomly swap pins while the robot is powered.

## Power domains

- Motor supply goes to TB6612 VM.
- ESP32 logic supply goes to TB6612 VCC at the correct logic voltage.
- Grounds must share a reference between motor controller and drivers.
- Jetson should use a regulator/power source appropriate for its board; do not power it through the motor-driver rail.

Keep motor-current wiring physically separated from future SDR/antenna wiring where practical.

## First physical test sequence

1. Put the chassis on blocks so all four wheels are off the floor.
2. Leave the ESP32 controller DISARMED.
3. Verify common ground and driver supply voltages.
4. Upload `firmware/esp32/esp32_motor_controller.ino`.
5. Connect ESP32 to Jetson/PC by USB.
6. Run dry-run first:

```bash
python3 src/main.py --mode motor-smoke
```

7. Confirm the printed wheel patterns make sense.
8. Only then run the physical low-speed test:

```bash
python3 src/main.py --mode motor-smoke --arm
```

The test sends only short low-amplitude commands and stops between patterns. The ESP32 watchdog disarms if serial commands stop.

## HC-SR04 warning

HC-SR04 modules are normally powered from 5 V and their ECHO output may reach 5 V. ESP32/XIAO/Jetson GPIO are 3.3 V-class inputs. Use a proper level shifter or resistor divider and verify the actual module before connecting its ECHO pin.

## Proximity sensors

The cylindrical sensors currently mounted on the chassis must be identified before wiring them to the control electronics. E18-D80NK-style sensors, if that is what they are, can have an output interface that should not be assumed compatible with 3.3 V GPIO without checking the exact module.

## RF stage

HackRF Pro integration will be receive-first. Mount the antenna away from the motors and power converters. Initial RF measurements should be collected while the motors are stopped to establish a self-EMI baseline.
