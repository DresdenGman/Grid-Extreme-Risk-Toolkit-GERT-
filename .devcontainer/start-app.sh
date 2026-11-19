#!/bin/bash
# Start GERT (web app + API) in the background if it is not already running.
# Runs on every Codespace start via postStartCommand in devcontainer.json.
# start.sh is non-interactive here: stdin is closed, output goes to a log.
if (exec 3<>/dev/tcp/127.0.0.1/3000) 2>/dev/null; then
  echo "GERT is already running (port 3000 is in use)."
  exit 0
fi
cd "$(dirname "$0")/.."
nohup bash start.sh </dev/null >/tmp/gert-start.log 2>&1 &
echo "GERT is starting: web app on port 3000, API on port 8000 (log: /tmp/gert-start.log)."
