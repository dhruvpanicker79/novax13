#!/usr/bin/env bash
# Rebuild the frontend in WSL and stage dist for the Windows-side server.
set -e
export PATH=$HOME/.local/bin:$PATH
W=/mnt/c/Users/nairb/SIH/novax_13
cp -r $W/frontend/src $W/frontend/index.html $W/frontend/vite.config.ts ~/kshetra/frontend/
mkdir -p ~/kshetra/frontend/public/data
cp ~/kshetra/data/demo/* ~/kshetra/frontend/public/data/ 2>/dev/null || true
cd ~/kshetra/frontend
npm run build 2>&1 | grep -E "built in|error|ERROR" | tail -4
rm -rf $W/dist.new && cp -r dist $W/dist.new
