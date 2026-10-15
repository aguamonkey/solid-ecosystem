"""A disposable SQLite API for browser tests; never opens development data."""
import tempfile
from pathlib import Path

import uvicorn
from field_notebook.http import create_app
from field_notebook.sqlite_store import SqliteNotebook, SqliteReceiptSink

with tempfile.TemporaryDirectory(prefix="ecosystem-browser-") as directory:
    store = SqliteNotebook(Path(directory) / "test.sqlite3")
    uvicorn.run(
        create_app(store, store, store, SqliteReceiptSink(store), root_path="/api"),
        host="127.0.0.1", port=8011,
    )
