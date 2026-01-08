from __future__ import annotations

"""Standard gamepad implementation backed by linux uinput."""

from dataclasses import dataclass
from typing import Dict, Iterable, List

import uinput

from .base_controller import BaseController


@dataclass(frozen=True)
class AxisSpec:
    code: int
    min_value: int
    max_value: int


BUTTONS: Dict[str, int] = {
    # Face buttons (south, east, west, north)
    "a": uinput.BTN_SOUTH,
    "b": uinput.BTN_EAST,
    "x": uinput.BTN_WEST,
    "y": uinput.BTN_NORTH,
    # Shoulder buttons
    "l1": uinput.BTN_TL,
    "r1": uinput.BTN_TR,
    "l2_click": uinput.BTN_TL2,
    "r2_click": uinput.BTN_TR2,
    # D-pad buttons (for browsers that expect button-based DPAD)
    "dpad_up": uinput.BTN_DPAD_UP,
    "dpad_down": uinput.BTN_DPAD_DOWN,
    "dpad_left": uinput.BTN_DPAD_LEFT,
    "dpad_right": uinput.BTN_DPAD_RIGHT,
    # Menu buttons
    "back": uinput.BTN_SELECT,
    "start": uinput.BTN_START,
    "guide": uinput.BTN_MODE,
    # Stick clicks
    "l3": uinput.BTN_THUMBL,
    "r3": uinput.BTN_THUMBR,
}

AXES: Dict[str, AxisSpec] = {
    # Left stick
    "lx": AxisSpec(uinput.ABS_X, -32768, 32767),
    "ly": AxisSpec(uinput.ABS_Y, -32768, 32767),
    # Right stick
    "rx": AxisSpec(uinput.ABS_RX, -32768, 32767),
    "ry": AxisSpec(uinput.ABS_RY, -32768, 32767),
    # Analog triggers
    "lt": AxisSpec(uinput.ABS_Z, 0, 255),
    "rt": AxisSpec(uinput.ABS_RZ, 0, 255),
    # D-pad hat
    "dpad_x": AxisSpec(uinput.ABS_HAT0X, -1, 1),
    "dpad_y": AxisSpec(uinput.ABS_HAT0Y, -1, 1),
}


class StandardGamepad(BaseController):
    def __init__(self, name: str = "Virtual Standard Gamepad") -> None:
        super().__init__(name)
        # Build proper event list with axis ranges for joysticks to work in browsers
        events: List = list(BUTTONS.values())
        
        # Add axes with proper min/max ranges so kernel exposes them correctly
        # Use the + operator to combine axis code with range tuple
        for axis_name, spec in AXES.items():
            events.append(spec.code + (spec.min_value, spec.max_value, 0, 0))
        
        # Use Xbox 360 USB IDs to align with the "standard" browser mapping and most tester sites
        # Vendor/Product: 0x045e/0x028e (Microsoft X360 Controller)
        self.device = uinput.Device(events, name=name, vendor=0x045E, product=0x028E, version=0x0110)

    def set_button(self, name: str, pressed: bool) -> None:
        key = name.lower()
        if key not in BUTTONS:
            raise KeyError(f"Unknown button '{name}'")
        self.device.emit(BUTTONS[key], 1 if pressed else 0)

    def set_axis(self, name: str, value: float) -> None:
        key = name.lower()
        if key not in AXES:
            raise KeyError(f"Unknown axis '{name}'")
        spec = AXES[key]
        scaled = self._scale(value, spec)

        # Mirror D-pad axes into button events so browser Gamepad API testers see DPAD
        if key == "dpad_x":
            self.device.emit(uinput.BTN_DPAD_LEFT, 1 if scaled < 0 else 0)
            self.device.emit(uinput.BTN_DPAD_RIGHT, 1 if scaled > 0 else 0)
        elif key == "dpad_y":
            self.device.emit(uinput.BTN_DPAD_UP, 1 if scaled < 0 else 0)
            self.device.emit(uinput.BTN_DPAD_DOWN, 1 if scaled > 0 else 0)

        self.device.emit(spec.code, scaled)

    def describe_layout(self) -> Dict[str, str]:
        description: Dict[str, str] = {}
        description.update({k: str(v) for k, v in BUTTONS.items()})
        description.update({k: str(v.code) for k, v in AXES.items()})
        return description

    @staticmethod
    def _scale(value: float, spec: AxisSpec) -> int:
        if spec.min_value >= 0:
            clamped = min(max(value, 0.0), 1.0)
            span = spec.max_value - spec.min_value
            return int(round(spec.min_value + clamped * span))
        clamped = min(max(value, -1.0), 1.0)
        span = spec.max_value - spec.min_value
        normalized = (clamped + 1.0) / 2.0  # map -1..1 to 0..1
        return int(round(spec.min_value + normalized * span))
