from __future__ import annotations

"""Virtual mouse controller for touchpad/aiming control."""

from typing import Dict

import uinput

from .base_controller import BaseController


class MouseController(BaseController):
    """Virtual mouse device for touchpad-based aiming."""
    
    def __init__(self, name: str = "Virtual Touchpad Mouse") -> None:
        super().__init__(name)
        # Create virtual mouse with movement and buttons
        events = [
            uinput.REL_X,
            uinput.REL_Y,
            uinput.BTN_LEFT,
            uinput.BTN_RIGHT,
            uinput.BTN_MIDDLE,
            uinput.REL_WHEEL,
            uinput.REL_HWHEEL,
        ]
        self.device = uinput.Device(events, name=name)
        
        # Track button states
        self.button_states = {
            "left": False,
            "right": False,
            "middle": False,
        }

    def set_button(self, name: str, pressed: bool) -> None:
        """Handle mouse button clicks."""
        key = name.lower()
        button_map = {
            "left": uinput.BTN_LEFT,
            "right": uinput.BTN_RIGHT,
            "middle": uinput.BTN_MIDDLE,
        }
        
        if key not in button_map:
            raise KeyError(f"Unknown mouse button '{name}'")
        
        self.device.emit(button_map[key], 1 if pressed else 0)
        self.button_states[key] = pressed

    def set_axis(self, name: str, value: float) -> None:
        """Handle relative mouse movement or scroll."""
        key = name.lower()
        
        # Relative movement (delta values)
        if key == "dx":
            # Scale float to pixel movement
            self.device.emit(uinput.REL_X, int(value))
        elif key == "dy":
            self.device.emit(uinput.REL_Y, int(value))
        elif key == "wheel":
            # Scroll wheel (usually -1, 0, or 1)
            self.device.emit(uinput.REL_WHEEL, int(value))
        elif key == "hwheel":
            # Horizontal scroll
            self.device.emit(uinput.REL_HWHEEL, int(value))
        else:
            raise KeyError(f"Unknown mouse axis '{name}'")

    def move_relative(self, dx: int, dy: int) -> None:
        """Move mouse cursor by relative amount."""
        if dx != 0:
            self.device.emit(uinput.REL_X, dx)
        if dy != 0:
            self.device.emit(uinput.REL_Y, dy)

    def scroll(self, amount: int) -> None:
        """Scroll wheel."""
        if amount != 0:
            self.device.emit(uinput.REL_WHEEL, amount)

    def describe_layout(self) -> Dict[str, str]:
        return {
            "left": "BTN_LEFT",
            "right": "BTN_RIGHT",
            "middle": "BTN_MIDDLE",
            "dx": "REL_X",
            "dy": "REL_Y",
            "wheel": "REL_WHEEL",
            "hwheel": "REL_HWHEEL",
        }
