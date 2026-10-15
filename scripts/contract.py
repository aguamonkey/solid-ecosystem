"""Generate/check the API contract without touching a database or starting a server."""
import argparse
import json
from pathlib import Path

from field_notebook.http import create_app
from field_notebook.memory import MemoryNotebook, MemoryReceiptSink

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
store = MemoryNotebook()
schema = create_app(store, store, store, MemoryReceiptSink(), root_path="/api").openapi()
schema["servers"] = [{"url": "/api"}]
rendered = json.dumps(schema, indent=2, sort_keys=True) + "\n"
target = ROOT / "contracts/openapi.json"
if args.check:
    if not target.exists() or target.read_text() != rendered:
        raise SystemExit("API contract changed. Run python scripts/contract.py and review the diff.")
    print("API contract matches the service.")
else:
    target.write_text(rendered)
