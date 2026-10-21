#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1
if [ ! -x .venv/bin/python ]; then
  echo "FreeFIDS is not installed yet. Run ./install_linux.sh first."
  exit 1
fi
exec .venv/bin/python app/launcher.py "$@"
