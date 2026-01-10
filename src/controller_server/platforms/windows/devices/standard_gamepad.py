from __future__ import annotations

"""Stub standard gamepad for Windows.

This keeps the package importable on Windows while we wire up a real
backend (e.g., ViGEmBus or vJoy). All mutating calls raise clear errors
so the API surface remains consistent with Linux devices.
"""

from typing import Dict

from ....devices.base_controller import BaseController


class StandardGamepad(BaseController):
    """Placeholder standard gamepad for Windows environments.

    Replace this with a concrete implementation when adding native
    Windows support (e.g., ViGEmBus for Xbox 360 controller emulation).
    """

    def __init__(self, name: str = "Windows Gamepad (stub)") -> None:
        super().__init__(name)

    def set_button(self, name: str, pressed: bool) -> None:  # pragma: no cover - placeholder
        raise NotImplementedError("Windows gamepad backend not implemented yet.")

    def set_axis(self, name: str, value: float) -> None:  # pragma: no cover - placeholder
        raise NotImplementedError("Windows gamepad backend not implemented yet.")

    def describe_layout(self) -> Dict[str, str]:  # pragma: no cover - placeholder
        return {}
