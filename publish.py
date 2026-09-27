"""Copy a freshly built dist over the served one without replacing the folder.

The Windows static server keeps a handle on the serve directory, so deleting
and renaming it fails. Copying file contents in place works because individual
files are not held open between requests.
"""
import os
import shutil
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "dist.new")
DST = os.path.join(ROOT, "dist")


def main() -> int:
    if not os.path.isdir(SRC):
        print(f"no build at {SRC}")
        return 1
    os.makedirs(DST, exist_ok=True)

    # Drop stale hashed bundles so the browser cannot serve an old chunk.
    assets = os.path.join(DST, "assets")
    if os.path.isdir(assets):
        for f in os.listdir(assets):
            try:
                os.remove(os.path.join(assets, f))
            except OSError:
                pass

    copied = 0
    for attempt in range(5):
        try:
            for root, _dirs, files in os.walk(SRC):
                rel = os.path.relpath(root, SRC)
                out = DST if rel == "." else os.path.join(DST, rel)
                os.makedirs(out, exist_ok=True)
                for f in files:
                    shutil.copy2(os.path.join(root, f), os.path.join(out, f))
                    copied += 1
            print(f"published {copied} files -> dist/")
            shutil.rmtree(SRC, ignore_errors=True)
            return 0
        except PermissionError as e:
            print(f"  locked ({e.filename}), retry {attempt + 1}/5")
            time.sleep(1.5)
    print("publish failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
