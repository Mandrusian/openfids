#!/usr/bin/env bash
# Adds FreeFIDS to your applications menu and (if you have one) your Desktop.
# Re-run this if you ever move the FreeFIDS folder.
ROOT="$(cd "$(dirname "$0")" && pwd)"
if [ ! -x "$ROOT/.venv/bin/python" ]; then
  echo "FreeFIDS is not installed yet. Run ./install_linux.sh first."
  exit 1
fi

APPS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$APPS"
ENTRY="$APPS/freefids.desktop"
cat > "$ENTRY" <<DESKTOP
[Desktop Entry]
Type=Application
Version=1.0
Name=FreeFIDS
GenericName=Flight Information Display
Comment=Cairns Airport FIDS (runs locally)
Exec="$ROOT/.venv/bin/python" "$ROOT/app/launcher.py"
Path=$ROOT
Icon=$ROOT/app/icon.png
Terminal=false
Categories=Utility;Network;
StartupNotify=false
DESKTOP
chmod +x "$ENTRY"
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS" >/dev/null 2>&1
echo "Menu entry: $ENTRY"

DESK="$(xdg-user-dir DESKTOP 2>/dev/null)"
[ -z "$DESK" ] && DESK="$HOME/Desktop"
if [ -d "$DESK" ]; then
  cp "$ENTRY" "$DESK/FreeFIDS.desktop"
  chmod +x "$DESK/FreeFIDS.desktop"
  # GNOME needs the launcher marked as trusted; harmless elsewhere
  command -v gio >/dev/null 2>&1 && gio set "$DESK/FreeFIDS.desktop" metadata::trusted true >/dev/null 2>&1
  echo "Desktop shortcut: $DESK/FreeFIDS.desktop"
  echo "(On GNOME/KDE you may need to right-click it once and choose 'Allow Launching'.)"
fi
