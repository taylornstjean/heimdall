# Copyright 2026 Taylor St Jean

import argparse
import socket
import threading
import time
import webbrowser

from heimdall_neo import __version__
from heimdall_neo.app import create_app


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="heimdall", description="Run the Heimdall local web app.")
    parser.add_argument("--host", default="127.0.0.1", help="interface to bind (default: %(default)s)")
    parser.add_argument("--port", type=int, default=8765, help="port to listen on (default: %(default)s)")
    parser.add_argument("--no-browser", action="store_true", help="don't open a browser window")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)

    browser_host = "127.0.0.1" if args.host in ("0.0.0.0", "::") else args.host
    url = f"http://{browser_host}:{args.port}"

    # open the browser if desired, will open by default
    if not args.no_browser:
        threading.Thread(target=_open_when_ready, args=(browser_host, args.port, url), daemon=True).start()

    app = create_app()
    from waitress import serve

    print(f"Heimdall {__version__} running at {url} (Ctrl+C to stop)", flush=True)
    serve(app, host=args.host, port=args.port)


def _open_when_ready(host: str, port: int, url: str, timeout: float = 10.0) -> None:
    """Wait until the server accepts connections, then open the page."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                webbrowser.open(url)
                return
        except OSError:
            time.sleep(0.1)
