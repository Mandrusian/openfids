#!/usr/bin/env bash
# OpenFIDS installer for Linux
set -u
cd "$(dirname "$0")" || exit 1
echo
echo " OpenFIDS - installer for Linux"
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

install_system_python() {
  local cmd=""
  if   command -v apt-get >/dev/null 2>&1; then cmd="sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip"
  elif command -v dnf     >/dev/null 2>&1; then cmd="sudo dnf install -y python3 python3-pip"
  elif command -v pacman  >/dev/null 2>&1; then cmd="sudo pacman -S --needed --noconfirm python python-pip"
  elif command -v zypper  >/dev/null 2>&1; then cmd="sudo zypper install -y python3 python3-pip python3-venv"
  elif command -v apk     >/dev/null 2>&1; then cmd="sudo apk add python3 py3-pip"
  fi
  if [ -z "$cmd" ]; then
    echo "Couldn't detect your package manager. Please install Python 3.9+ (with venv and pip) and re-run."
    return 1
  fi
  echo "This will run: $cmd"
  read -r -p "Go ahead? [Y/n] " a
  [[ "$a" =~ ^[Nn] ]] && return 1
  bash -c "$cmd"
}

PY="$(pick_python)" || PY=""
if [ -z "$PY" ]; then
  echo "Python 3.9 or newer was not found."
  install_system_python || exit 1
  PY="$(pick_python)" || { echo "Python still not found."; exit 1; }
fi
echo "Using $($PY --version) at $(command -v "$PY")"

echo "[1/3] Creating private environment in .venv ..."
if [ ! -x .venv/bin/python ]; then
  rm -rf .venv
  if ! "$PY" -m venv .venv >/dev/null 2>&1; then
    echo "Python's venv module is missing."
    install_system_python || exit 1
    rm -rf .venv
    "$PY" -m venv .venv || { echo "Could not create the environment."; exit 1; }
  fi
fi

echo "[2/3] Installing requirements ..."
.venv/bin/python -m pip install --upgrade pip >/dev/null 2>&1
.venv/bin/python -m pip install -r app/requirements.txt || { echo "Install failed. Check your internet connection."; exit 1; }

echo "[3/3] Creating menu entry and desktop shortcut ..."
bash ./shortcut_linux.sh

echo
echo " All done! Find OpenFIDS in your applications menu, or run ./start_linux.sh"
read -r -p "Start OpenFIDS now? [Y/n] " a
[[ "$a" =~ ^[Nn] ]] || { nohup .venv/bin/python app/launcher.py >/dev/null 2>&1 & disown; }
