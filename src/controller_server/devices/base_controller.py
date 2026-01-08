from __future__ import annotations

"""Abstract controller base class for virtual uinput devices."""

import abc
from typing import Dict


class BaseController(abc.ABC):
    def __init__(self, name: str) -> None:
        self.name = name

    @abc.abstractmethod
    def set_button(self, name: str, pressed: bool) -> None:
        """Update the state of a button."""

    @abc.abstractmethod
    def set_axis(self, name: str, value: float) -> None:
        """Update the state of an axis or hat value."""

    @abc.abstractmethod
    def describe_layout(self) -> Dict[str, str]:
        """Return a mapping of available logical inputs to their device codes."""

    def close(self) -> None:
        """Hook for controllers that need cleanup."""
        # Most uinput devices do not require explicit teardown.
        return
