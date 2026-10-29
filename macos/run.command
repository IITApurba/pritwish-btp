#!/bin/bash
# Starts the web app on macOS and opens it in the browser.
cd "$(dirname "$0")/.." || exit 1

if [ ! -x .venv/bin/python ]; then
  echo "Setup has not been run yet - running it now."
  bash macos/setup.command --no-pause || { read -r -p "Setup failed, so the app cannot start. Press Enter to close..."; exit 1; }
fi

echo "Starting the app at http://127.0.0.1:5001  (press Ctrl+C to stop)"
(sleep 2 && open "http://127.0.0.1:5001") &
.venv/bin/python app.py
