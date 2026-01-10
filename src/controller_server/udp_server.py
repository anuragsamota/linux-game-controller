from __future__ import annotations

"""Standalone UDP server entrypoint (no WebSocket server)."""

import argparse
import asyncio
import logging

from .device_registry import DeviceRegistry
from .librepad_udp import LibrePadUDPServer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Virtual controller UDP server (standalone)")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface to bind")
    parser.add_argument("--port", type=int, default=9775, help="UDP port to listen on")
    return parser.parse_args()


async def run_udp_server(host: str, port: int) -> None:
    """Run standalone UDP server."""
    registry = DeviceRegistry()
    udp_server = LibrePadUDPServer(host=host, port=port)
    udp_server.set_device_registry(registry)
    
    logger.info("Starting standalone UDP server on %s:%s", host, port)
    
    try:
        await udp_server.start()
    except asyncio.CancelledError:
        logger.info("UDP server shutting down")
    except Exception as exc:
        logger.error("UDP server error: %s", exc)
        raise


def main() -> None:
    args = parse_args()
    
    try:
        asyncio.run(run_udp_server(host=args.host, port=args.port))
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down")


if __name__ == "__main__":
    main()
