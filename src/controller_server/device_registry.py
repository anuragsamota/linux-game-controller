"""Shared device registry for virtual controllers.

This module provides a transport-agnostic device management layer
that can be used by any interface (WebSocket, WebRTC, etc.).
The registry creates/destroys uinput devices on demand based on client connections.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, Iterable, Optional

from .devices.base_controller import BaseController
from .devices.standard_gamepad import StandardGamepad
from .devices.mouse_controller import MouseController

logger = logging.getLogger(__name__)


class DeviceRegistry:
    """Creates and reuses controller instances by logical name.
    
    Devices are created lazily on first connection and destroyed when no clients remain.
    This enables safe plug-and-play without manual /proc manipulation.
    """

    def __init__(self) -> None:
        self._constructors = {
            "standard": StandardGamepad,
            "mouse": MouseController,
        }
        self._instances: Dict[str, BaseController] = {}
        self._client_counts: Dict[str, int] = {}
        self._lock = asyncio.Lock()

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
