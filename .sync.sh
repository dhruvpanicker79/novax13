#!/usr/bin/env bash
# Rebuild in WSL and publish dist to the Windows side for serving.
set -e
export PATH=$HOME/.local/bin:$PATH
W=/mnt/c/Users/nairb/SIH/novax_13
cp -r $W/frontend/src $W/frontend/index.html $W/frontend/vite.config.ts ~/bhoomisetu/frontend/
cd ~/bhoomisetu/frontend
npm run build 2>&1 | grep -E "built in|error|ERROR" | tail -4
rm -rf $W/dist.new && cp -r dist $W/dist.new
