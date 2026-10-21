#!/bin/bash
# Creates FreeFIDS.app in ~/Applications and a link on the Desktop.
# Re-run this if you ever move the FreeFIDS folder.
ROOT="$(cd "$(dirname "$0")" && pwd)"
if [ ! -x "$ROOT/.venv/bin/python" ]; then
  echo "FreeFIDS is not installed yet. Run install_macos.command first."
  read -r -p "Press Enter to close..." _; exit 1
fi

APP="$HOME/Applications/FreeFIDS.app"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp "$ROOT/app/icon.icns" "$APP/Contents/Resources/FreeFIDS.icns"

cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>FreeFIDS</string>
  <key>CFBundleDisplayName</key><string>FreeFIDS</string>
  <key>CFBundleIdentifier</key><string>local.freefids.app</string>
  <key>CFBundleExecutable</key><string>FreeFIDS</string>
  <key>CFBundleIconFile</key><string>FreeFIDS</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleVersion</key><string>1.0</string>
  <key>LSUIElement</key><false/>
</dict></plist>
PLIST

cat > "$APP/Contents/MacOS/FreeFIDS" <<LAUNCH
#!/bin/bash
exec "$ROOT/.venv/bin/python" "$ROOT/app/launcher.py" >> "\$HOME/Library/Application Support/FreeFIDS/freefids.log" 2>&1
LAUNCH
mkdir -p "$HOME/Library/Application Support/FreeFIDS"
chmod +x "$APP/Contents/MacOS/FreeFIDS"
touch "$APP"

ln -sfn "$APP" "$HOME/Desktop/FreeFIDS" 2>/dev/null

echo "Created: $APP"
echo "Desktop link: ~/Desktop/FreeFIDS"
[ "$1" = "nopause" ] || read -r -p "Press Enter to close..." _
