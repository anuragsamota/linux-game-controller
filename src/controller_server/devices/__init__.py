"""Shared device interfaces (platform-agnostic).

Platform-specific implementations live under `platforms/` and are imported
lazily by registries to avoid importing unavailable backends.
"""

from .base_controller import BaseController

__all__ = ["BaseController"]
