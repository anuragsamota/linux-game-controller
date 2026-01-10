"""Shared device registry for virtual controllers.

This module provides a transport-agnostic device management layer
that can be used by any interface (WebSocket, etc.).
Devices are created lazily based on client connections.

Platform awareness:
- Linux: backed by uinput (StandardGamepad, MouseController)
- Windows: placeholder controllers are provided so imports work; real
    Windows backend (e.g., ViGEm/vJoy) can be plugged in later without
    refactoring server code.
"""

from __future__ import annotations

import asyncio
import logging
import platform
from typing import Dict, Iterable, Optional, Type

from .devices.base_controller import BaseController

logger = logging.getLogger(__name__)


class DeviceRegistry:
    """Creates and reuses controller instances by logical name.
    
    Devices are created lazily on first connection and destroyed when no clients remain.
    This enables safe plug-and-play without manual /proc manipulation.
    """

    def __init__(self) -> None:
        self._constructors = self._load_platform_constructors()
        self._instances: Dict[str, BaseController] = {}
        self._client_counts: Dict[str, int] = {}
        self._lock = asyncio.Lock()

    def _load_platform_constructors(self) -> Dict[str, Type[BaseController]]:
        """Load device constructors for the current platform without
        importing platform-specific backends on unsupported OSes.
        """
        system = platform.system().lower()

        if system == "linux":
            # Import uinput-backed controllers only when running on Linux
            from .platforms.linux.devices.standard_gamepad import StandardGamepad
            from .platforms.linux.devices.mouse_controller import MouseController

            return {
                "standard": StandardGamepad,
                "mouse": MouseController,
            }

        if system == "windows":
            # Stub for future Windows implementation (e.g., ViGEm/vJoy)
            from .platforms.windows.devices.standard_gamepad import StandardGamepad

            return {
                "standard": StandardGamepad,
            }

        raise RuntimeError(f"Unsupported platform: {system}. Only Linux is fully supported today.")

    async def acquire(self, name: str, display_name: str | None = None) -> BaseController:
        """Get or create a device, tracking client ownership.
        
        Args:
            name: Device type (e.g., 'standard')
            display_name: Optional display name for the uinput device (set at creation, immutable after)
        """
        key = name.lower()
        if key not in self._constructors:
            available = ', '.join(self._constructors.keys())
            raise KeyError(f"Unknown controller type '{name}'. Available: {available}")
        
        async with self._lock:
            # Lazily create on first use
            if key not in self._instances:
                logger.info("Creating device: %s", key)
                # Pass display_name to the device constructor
                self._instances[key] = self._constructors[key](name=display_name or key)
                self._client_counts[key] = 0
            
            # Increment client count
            self._client_counts[key] += 1
            if self._client_counts[key] == 1:
                logger.info("Device %s activated (1 client)", key)
            else:
                logger.debug("Device %s now has %d clients", key, self._client_counts[key])
            return self._instances[key]

    async def release(self, name: str) -> None:
        """Decrement client count; destroy device if no clients remain."""
        key = name.lower()
        if key not in self._instances:
            return
        
        async with self._lock:
            self._client_counts[key] = max(0, self._client_counts[key] - 1)
            
            # Destroy device when last client leaves
            if self._client_counts[key] == 0:
                logger.info("Destroying device: %s (no clients)", key)
                device = self._instances.pop(key)
                del self._client_counts[key]
                device.close()
            else:
                logger.debug("Device %s now has %d clients", key, self._client_counts[key])

    def get(self, name: str) -> Optional[BaseController]:
        """Get an existing controller instance if present."""
        return self._instances.get(name.lower())

    def available(self) -> Iterable[str]:
        """Return list of available controller types."""
        return self._constructors.keys()
