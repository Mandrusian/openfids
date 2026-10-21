"""Starts OpenFIDS locally and opens it in your browser.

Usage:  python launcher.py            open in the default browser (default)
        python launcher.py --window   open in a native window (needs: pip install pywebview)
        python launcher.py --no-open  just run the server
"""
import argparse
import json
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# pythonw (Windows, no console) has no stdout/stderr; send them to a log file.
if sys.stdout is None or sys.stderr is None:
    from server import DATA_DIR
    log = open(DATA_DIR / "openfids.log", "a", buffering=1, encoding="utf-8")
    sys.stdout = sys.stderr = log

import uvicorn  # noqa: E402

HOST = "127.0.0.1"
FIRST_PORT = 8000


def is_openfids(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://{HOST}:{port}/api/status", timeout=1.5) as r:
            return json.load(r).get("app") == "openfids"
    except Exception:
        return False


def port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((HOST, port)) != 0


def wait_until_up(port: int, timeout: float = 20) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if is_openfids(port):
            return True
        time.sleep(0.2)
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--window", action="store_true", help="use a native window instead of the browser")
    parser.add_argument("--no-open", action="store_true", help="don't open anything, just serve")
    args = parser.parse_args()

    # Already running (e.g. shortcut clicked twice)? Just open it again.
    for port in range(FIRST_PORT, FIRST_PORT + 20):
        if is_openfids(port):
            if not args.no_open:
                webbrowser.open(f"http://{HOST}:{port}")
            return
    port = next((p for p in range(FIRST_PORT, FIRST_PORT + 20) if port_free(p)), None)
    if port is None:
        print("No free port found between 8000 and 8019.")
        sys.exit(1)

    url = f"http://{HOST}:{port}"
    from server import app

    print(f"OpenFIDS is running at {url}")
    print("Close this window (or press Ctrl+C) to stop it.")

    if args.window:
        try:
            import webview
        except ImportError:
            print("pywebview is not installed; falling back to the browser.")
            args.window = False

    if args.window:
        threading.Thread(
            target=lambda: uvicorn.run(app, host=HOST, port=port, log_level="warning", log_config=None),
            daemon=True,
        ).start()
        wait_until_up(port)
        webview.create_window("Cairns Airport FIDS", url, width=1400, height=900, min_size=(900, 600))
        webview.start()
        return

    if not args.no_open:
        def opener():
            if wait_until_up(port):
                webbrowser.open(url)
        threading.Thread(target=opener, daemon=True).start()

    uvicorn.run(app, host=HOST, port=port, log_level="warning", log_config=None)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
