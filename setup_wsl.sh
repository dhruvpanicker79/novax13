#!/usr/bin/env bash
# One-shot environment setup for BhoomiSetu inside WSL2 / Ubuntu.
#
# Run from the project root:
#     bash setup_wsl.sh
#
# Smart App Control is a Windows code-integrity policy. It does not apply to
# processes inside the WSL Linux userspace, so the whole scientific stack --
# including pyproj, rasterio, GDAL and scikit-learn, all of which SAC blocks on
# the Windows side -- installs and runs normally here.
set -euo pipefail

BOLD=$'\033[1m'; DIM=$'\033[2m'; OK=$'\033[32m'; WARN=$'\033[33m'; OFF=$'\033[0m'
step() { echo; echo "${BOLD}==> $*${OFF}"; }

step "Checking we are actually inside WSL"
if ! grep -qiE "(microsoft|wsl)" /proc/version 2>/dev/null; then
  echo "${WARN}This does not look like WSL.${OFF}"
  echo "On Windows, run in an ADMIN PowerShell:   wsl --install"
  echo "then reboot, open Ubuntu, cd to this project and re-run."
  exit 1
fi
echo "${OK}WSL detected:${OFF} $(grep -o 'Microsoft.*' /proc/version | head -1)"

step "System packages"
sudo apt-get update -qq
# libgdal-dev and libgeos-dev let rasterio/shapely build if no wheel matches.
# Use whatever python3 the distro ships (Ubuntu 24.04 = 3.12, 22.04 = 3.10).
# Every dependency supports 3.10+, so pinning a version only creates failures.
sudo apt-get install -y -qq \
  python3 python3-venv python3-pip \
  build-essential libgeos-dev libproj-dev libgdal-dev gdal-bin \
  curl git

step "Node.js 20 (for the frontend)"
if ! command -v node >/dev/null 2>&1; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt-get install -y -qq nodejs
fi
echo "${OK}node${OFF} $(node --version)   ${OK}npm${OFF} $(npm --version)"

step "Python virtual environment"
PY=$(command -v python3)
echo "using $PY ($($PY --version))"
$PY -m venv .venv-linux
# shellcheck disable=SC1091
source .venv-linux/bin/activate
python -m pip install -q --upgrade pip wheel setuptools

step "Python dependencies"
python -m pip install -q -r requirements.txt

step "Verifying the full stack imports"
python - <<'PY'
import importlib, sys
mods = ["numpy", "scipy", "shapely", "pandas", "xgboost",
        "fastapi", "pydantic", "pyproj", "rasterio", "sklearn", "requests"]
bad = []
for m in mods:
    try:
        mod = importlib.import_module(m)
        print(f"  ok   {m:<12} {getattr(mod, '__version__', '?')}")
    except Exception as ex:
        bad.append(m)
        print(f"  FAIL {m:<12} {type(ex).__name__}: {ex}")
if bad:
    sys.exit(f"\nblocked or missing: {', '.join(bad)}")
print("\nall imports clean")
PY

step "Running the engine verification suite"
# Verification failing here is information, not a setup error: it means the
# environment is fine and the engine needs work. Do not abort the script.
set +e
PYTHONPATH=backend python scripts/verify_all.py
VERIFY_RC=$?
set -e
if [ $VERIFY_RC -ne 0 ]; then
  echo
  echo "${WARN}Verification reported failures (exit $VERIFY_RC).${OFF}"
  echo "The environment is fine — this is the engine telling us what to fix."
fi

cat <<EOF

${OK}${BOLD}Environment ready.${OFF}

  activate      source .venv-linux/bin/activate
  verify        PYTHONPATH=backend python scripts/verify_all.py
  fetch data    PYTHONPATH=backend python scripts/fetch_data.py chandausi pune
  api           PYTHONPATH=backend uvicorn api.main:app --reload --port 8000

${DIM}Note: keep the project on the Linux filesystem (e.g. ~/bhoomisetu) rather than
/mnt/c — cross-filesystem I/O in WSL is roughly 10x slower, which matters when
parsing the 77 MB Microsoft footprint tiles.${OFF}
EOF
