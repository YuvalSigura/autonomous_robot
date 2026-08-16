from src.robot.mecanum import WheelCommand, mix_mecanum


def test_forward_all_wheels_same_sign():
    cmd = mix_mecanum(0.2, 0.0, 0.0)
    assert cmd == WheelCommand(0.2, 0.2, 0.2, 0.2)


def test_strafe_right_pattern():
    cmd = mix_mecanum(0.0, 0.2, 0.0)
    assert cmd == WheelCommand(-0.2, 0.2, 0.2, -0.2)


def test_rotation_pattern():
    cmd = mix_mecanum(0.0, 0.0, 0.2)
    assert cmd == WheelCommand(-0.2, 0.2, -0.2, 0.2)


def test_polarity_is_configurable():
    cmd = WheelCommand(0.2, 0.2, 0.2, 0.2).with_polarity(1, -1, 1, -1)
    assert cmd == WheelCommand(0.2, -0.2, 0.2, -0.2)
