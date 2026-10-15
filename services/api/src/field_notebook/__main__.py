import argparse
import logging
from pathlib import Path

import uvicorn

from .http import create_app
from .memory import MemoryNotebook, MemoryReceiptSink
from .sqlite_store import SqliteNotebook, SqliteReceiptSink


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local Field Notebook backend")
    storage = parser.add_mutually_exclusive_group()
    storage.add_argument("--database", type=Path, default=Path("data/notebook.sqlite3"))
    storage.add_argument(
        "--memory", action="store_true", help="Use ephemeral memory storage"
    )
    parser.add_argument("--port", type=int, default=8010)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--root-path", default="")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    if args.memory:
        memory = MemoryNotebook()
        app = create_app(
            memory, memory, memory, MemoryReceiptSink(), root_path=args.root_path
        )
    else:
        store = SqliteNotebook(args.database)
        app = create_app(
            store, store, store, SqliteReceiptSink(store), root_path=args.root_path
        )
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
