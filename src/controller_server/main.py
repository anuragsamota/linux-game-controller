from __future__ import annotations

"""CLI entrypoint for running the controller server."""

import argparse

from .server import run_server


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Virtual controller WebSocket server")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface to bind")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
