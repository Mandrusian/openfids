#!/bin/bash
cd "$(dirname "$0")" || exit 1
if [ ! -x .venv/bin/python ]; then
  echo "OpenFIDS is not installed yet. Run install_macos.command first."
  read -r -p "Press Enter to close..." _; exit 1
fi
exec .venv/bin/python app/launcher.py "$@"
