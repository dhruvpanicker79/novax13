#!/usr/bin/env bash
# Bootstrap the WSL environment WITHOUT sudo.
#
# Constraint: the Ubuntu user has no passwordless sudo, so apt is unavailable.
# Both blockers are solvable anyway:
#   * Python  -- python3-venv is already present; the venv bootstraps its own pip
#   * Node.js -- official linux-x64 tarball unpacked into ~/.local, no root needed
set -e

SRC=/mnt/c/Users/nairb/SIH/novax_13
DST=$HOME/bhoomisetu

echo "=== copying project to the Linux filesystem ==="
rm -rf "$DST"
mkdir -p "$DST"
cd "$SRC"
cp -r backend scripts data docs "$DST"/ 2>/dev/null || true
cp ./*.md ./*.txt ./*.sh "$DST"/ 2>/dev/null || true
rm -rf "$DST/data/raw/_cache"
du -sh "$DST"

echo "=== python venv ==="
cd "$DST"
# ensurepip ships in python3.12-venv, which needs apt. Build the venv without
# pip and bootstrap pip into it from get-pip.py instead -- same end state,
# no root required.
python3 -m venv --without-pip .venv
curl -fsSL -o /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py
.venv/bin/python /tmp/get-pip.py -q 2>&1 | tail -2
.venv/bin/python -m pip install -q --upgrade pip wheel setuptools 2>&1 | tail -2

echo "=== installing numeric stack ==="
.venv/bin/python -m pip install -q \
  numpy scipy shapely pandas xgboost requests pyproj 2>&1 | tail -3

echo "=== import test ==="
.venv/bin/python - <<'PY'
import numpy, scipy, shapely, pandas, xgboost, pyproj
for m in (numpy, scipy, shapely, pandas, xgboost, pyproj):
    print(f"  {m.__name__:<10} {m.__version__}")
PY

echo "=== node 20 (tarball into ~/.local, no sudo) ==="
if [ ! -x "$HOME/.local/bin/node" ]; then
  mkdir -p "$HOME/.local"
  cd /tmp
  NODE=v20.18.1
  curl -fsSL -o node.tar.xz \
    "https://nodejs.org/dist/$NODE/node-$NODE-linux-x64.tar.xz"
  tar -xJf node.tar.xz
  cp -r "node-$NODE-linux-x64"/* "$HOME/.local/"
  rm -rf node.tar.xz "node-$NODE-linux-x64"
fi
export PATH="$HOME/.local/bin:$PATH"
grep -q 'HOME/.local/bin' "$HOME/.bashrc" 2>/dev/null || \
  echo 'export PATH=$HOME/.local/bin:$PATH' >> "$HOME/.bashrc"
echo "  node $(node --version)   npm $(npm --version)"

echo "SETUP_COMPLETE"
