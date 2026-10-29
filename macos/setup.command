#!/bin/bash
# One-time setup for macOS: creates .venv in the project folder and installs the requirements.
# run.command calls this with --no-pause so the window does not stop before the app starts.
cd "$(dirname "$0")/.." || exit 1
[ "$1" = "--no-pause" ] && NO_PAUSE=1

finish() {  # finish <exit code> <message>
  echo
  echo "$2"
  [ "$NO_PAUSE" = 1 ] || read -r -p "Press Enter to close..."
  exit "$1"
}

if ! command -v python3 >/dev/null 2>&1 || ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null; then
  finish 1 "Python 3.9 or newer was not found. Install it from https://www.python.org/downloads/ and run this again."
fi

# Create .venv, or rebuild it if it is missing or broken.
if ! .venv/bin/python -c 'import sys' >/dev/null 2>&1; then
  echo "Creating virtual environment..."
  python3 -m venv --clear .venv || finish 1 "Could not create .venv."
fi

echo "Installing requirements (this can take a few minutes)..."
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt \
  || finish 1 "Setup failed. Check your internet connection and the messages above, then run this again."

finish 0 "Setup complete. Now double-click macos/run.command to start the app."
