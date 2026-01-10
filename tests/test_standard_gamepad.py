from __future__ import annotations

"""Unit tests for the StandardGamepad using a fake uinput backend."""

import importlib
import sys
import types
import unittest
from pathlib import Path

# Ensure project src is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC))


def make_fake_uinput() -> types.ModuleType:
    mod = types.ModuleType("uinput")

    # Button codes
    mod.BTN_SOUTH = 304
    mod.BTN_EAST = 305
    mod.BTN_WEST = 307
    mod.BTN_NORTH = 308
    mod.BTN_TL = 310
    mod.BTN_TR = 311
    mod.BTN_TL2 = 312
    mod.BTN_TR2 = 313
    mod.BTN_START = 315
    mod.BTN_SELECT = 314
    mod.BTN_MODE = 316
    mod.BTN_THUMBL = 317
    mod.BTN_THUMBR = 318
    mod.BTN_DPAD_UP = 544
    mod.BTN_DPAD_DOWN = 545
    mod.BTN_DPAD_LEFT = 546
    mod.BTN_DPAD_RIGHT = 547

    # Axis codes (make them support + operator for ranges)
    class AxisCode(int):
        def __add__(self, other):
            if isinstance(other, tuple):
                return (int(self),) + other
            return super().__add__(other)
    
    mod.ABS_X = AxisCode(0)
    mod.ABS_Y = AxisCode(1)
    mod.ABS_RX = AxisCode(3)
    mod.ABS_RY = AxisCode(4)
    mod.ABS_Z = AxisCode(2)
    mod.ABS_RZ = AxisCode(5)
    mod.ABS_HAT0X = AxisCode(16)
    mod.ABS_HAT0Y = AxisCode(17)

    class FakeDevice:
        def __init__(self, events, name=None, vendor=None, product=None, version=None):
            self.events = events
            self.name = name
            self.vendor = vendor
            self.product = product
            self.version = version
            self.emitted = []
            mod.last_device = self

        def emit(self, code, value):
            self.emitted.append((code, value))

    mod.Device = FakeDevice
    return mod


# Install fake uinput before importing the module under test
_fake_uinput = make_fake_uinput()
_original_uinput = sys.modules.get("uinput")
sys.modules["uinput"] = _fake_uinput

from controller_server.platforms.linux.devices.standard_gamepad import AXES, BUTTONS, StandardGamepad  # noqa: E402


class StandardGamepadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gamepad = StandardGamepad(name="TestPad")
        self.fake_device = _fake_uinput.last_device

    @classmethod
    def tearDownClass(cls) -> None:
        # Restore real uinput if it was present
        if _original_uinput is not None:
            sys.modules["uinput"] = _original_uinput
        else:
            sys.modules.pop("uinput", None)

    def test_button_press_emits_event(self) -> None:
        self.gamepad.set_button("a", True)
        self.assertIn((BUTTONS["a"], 1), self.fake_device.emitted)

    def test_axis_scaling_for_stick(self) -> None:
        spec = AXES["lx"]
        self.gamepad.set_axis("lx", -1.0)
        self.gamepad.set_axis("lx", 1.0)
        self.assertIn((spec.code, spec.min_value), self.fake_device.emitted)
        self.assertIn((spec.code, spec.max_value), self.fake_device.emitted)

    def test_trigger_scaling_zero_to_one(self) -> None:
        spec = AXES["lt"]
        self.gamepad.set_axis("lt", 0.0)
        self.gamepad.set_axis("lt", 1.0)
        self.assertIn((spec.code, spec.min_value), self.fake_device.emitted)
        self.assertIn((spec.code, spec.max_value), self.fake_device.emitted)

    def test_dpad_discrete_values(self) -> None:
        spec = AXES["dpad_x"]
        self.gamepad.set_axis("dpad_x", 1)
        self.gamepad.set_axis("dpad_x", -1)
        self.assertIn((spec.code, 1), self.fake_device.emitted)
        self.assertIn((spec.code, -1), self.fake_device.emitted)

    def test_unknown_button_raises(self) -> None:
        with self.assertRaises(KeyError):
            self.gamepad.set_button("invalid", True)

    def test_unknown_axis_raises(self) -> None:
        with self.assertRaises(KeyError):
            self.gamepad.set_axis("invalid", 0.0)


if __name__ == "__main__":
    unittest.main()
