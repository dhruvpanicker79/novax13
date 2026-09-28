"""Static server for the built app, with caching disabled.

`python -m http.server` sends no cache headers, so browsers apply heuristic
caching and will happily keep serving a stale index.html that points at a
deleted asset bundle. That cost real debugging time once and would be far
worse mid-demo, where the symptom is "the feature I just added is missing"
with no error anywhere.

    python serve.py [port]
"""
from __future__ import annotations

import os
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, fmt, *args):
        # Only surface problems; a scrolling 200 log hides the one 404 that
        # matters.
        status = args[1] if len(args) > 1 else ""
        if str(status).startswith(("4", "5")):
            sys.stderr.write(f"  {self.path} -> {status}\n")


def main() -> int:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    if not os.path.isdir(ROOT):
        print(f"no build at {ROOT} — run the frontend build first")
        return 1
    handler = partial(Handler, directory=ROOT)
    srv = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"\n  KSHETRA  ->  http://127.0.0.1:{port}")
    print("  caching disabled; Ctrl+C to stop\n")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
