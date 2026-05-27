from __future__ import annotations

import argparse
from pathlib import Path

import uvicorn

from .api import create_app


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the ERMI Command Center API.")
    parser.add_argument("--root", type=Path, default=Path("archive"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)

    uvicorn.run(create_app(args.root), host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

