#!/bin/bash
# FreeFIDS installer for macOS (double-click to run)
cd "$(dirname "$0")" || exit 1
echo
echo " FreeFIDS - installer for macOS"
echo " =============================="
echo

pick_python() {
  for c in python3.13 python3.12 python3.11 python3.10 python3.9 python3; do
    if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)' >/dev/null 2>&1; then
      echo "$c"; return 0
    fi
  done
  return 1
}

PY="$(pick_python)"
if [ -z "$PY" ]; then
  echo "Python 3.9 or newer was not found."
  if command -v brew >/dev/null 2>&1; then
    read -r -p "Install Python with Homebrew now? [Y/n] " a
    if [[ ! "$a" =~ ^[Nn] ]]; then
      brew install python || exit 1
      PY="$(pick_python)"
    fi
  fi
  if [ -z "$PY" ]; then
    echo "Please install Python from https://www.python.org/downloads/macos/ and run this again."
    open "https://www.python.org/downloads/macos/" 2>/dev/null
    read -r -p "Press Enter to close..." _; exit 1
  fi
fi
echo "Using $($PY --version) at $(command -v "$PY")"

echo "[1/3] Creating private environment in .venv ..."
[ -x .venv/bin/python ] || "$PY" -m venv .venv || { echo "Could not create the environment."; read -r -p "Press Enter..." _; exit 1; }

echo "[2/3] Installing requirements ..."
.venv/bin/python -m pip install --upgrade pip >/dev/null 2>&1
.venv/bin/python -m pip install -r app/requirements.txt || { echo "Install failed. Check your internet connection."; read -r -p "Press Enter..." _; exit 1; }

echo "[3/3] Creating the FreeFIDS app ..."
bash ./shortcut_macos.command nopause

echo
echo " All done! Open FreeFIDS from Launchpad / Applications or your Desktop."
read -r -p "Start FreeFIDS now? [Y/n] " a
[[ "$a" =~ ^[Nn] ]] || nohup .venv/bin/python app/launcher.py >/dev/null 2>&1 &
sleep 1
