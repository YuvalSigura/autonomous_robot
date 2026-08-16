from src.robot.mecanum import WheelCommand
from src.robot.serial_link import MotorControllerLink, MotorLinkConfig


def test_dry_run_requires_arm_before_wheels():
    link = MotorControllerLink(MotorLinkConfig(), dry_run=True)
    try:
        link.send_wheels(WheelCommand(0.1, 0.1, 0.1, 0.1))
    except RuntimeError:
        pass
    else:
        raise AssertionError("wheel command should require explicit arm")


def test_dry_run_arm_ping_and_stop():
    with MotorControllerLink(MotorLinkConfig(), dry_run=True) as link:
        assert link.ping().startswith("PONG")
        link.arm()
        link.send_wheels(WheelCommand(0.1, 0.1, 0.1, 0.1))
        link.stop()
        link.disarm()
