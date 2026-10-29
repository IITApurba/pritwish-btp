#!/bin/bash
# One-time setup for macOS: creates .venv in the project folder and installs the requirements.
cd "$(dirname "$0")/.." || exit 1

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 was not found. Install it from https://www.python.org/downloads/ and run this again."
  read -r -p "Press Enter to close..."
  exit 1
fi

if [ ! -d .venv ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv || { read -r -p "Could not create .venv. Press Enter to close..."; exit 1; }
fi

echo "Installing requirements (this can take a few minutes)..."
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt || { read -r -p "Install failed. Press Enter to close..."; exit 1; }

echo
echo "Setup complete. Now double-click macos/run.command to start the app."
read -r -p "Press Enter to close..."
