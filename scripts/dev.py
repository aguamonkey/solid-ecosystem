"""Run only owned child processes; Ctrl+C shuts both down without deleting data."""
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    for port in (8010, 5180):
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                raise SystemExit(f"Port {port} is occupied. Stop that server first.")
    children = []
    try:
        children.append(subprocess.Popen(
            [sys.executable, "-m", "field_notebook", "--port", "8010",
             "--database", str(ROOT / "data/notebook.sqlite3"), "--root-path", "/api"],
            cwd=ROOT, start_new_session=True,
        ))
        children.append(subprocess.Popen(
            ["npm", "run", "dev"], cwd=ROOT / "apps/web", start_new_session=True,
        ))
        print("Dashboard: http://127.0.0.1:5180 | API: http://127.0.0.1:5180/api/docs", flush=True)
        while all(child.poll() is None for child in children):
            time.sleep(0.3)
        raise SystemExit("A development server stopped; shutting down its companion.")
    except KeyboardInterrupt:
        pass
    finally:
        for child in children:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
        for child in children:
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()


if __name__ == "__main__":
    main()
