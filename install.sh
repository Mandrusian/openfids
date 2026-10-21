#!/usr/bin/env bash
# OpenFIDS one-line installer for Linux and macOS.
#   curl -fsSL https://raw.githubusercontent.com/Mandrusian/openfids/main/install.sh | bash
# Options (environment variables):
#   OPENFIDS_DIR=/some/path   where to install (default: ~/openfids)
#   OPENFIDS_REF=v1.0         branch, tag or commit to install (default: main)
set -euo pipefail

REPO="Mandrusian/openfids"
REF="${OPENFIDS_REF:-main}"
DEST="${OPENFIDS_DIR:-$HOME/openfids}"

# Everything lives in main() so a half-downloaded script can't run partially.
main() {
  for tool in curl tar; do
    command -v "$tool" >/dev/null 2>&1 || { echo "OpenFIDS installer needs '$tool'. Please install it and retry."; exit 1; }
  done

  case "$(uname -s)" in
    Linux)  INSTALLER="install_linux.sh" ;;
    Darwin) INSTALLER="install_macos.command" ;;
    *) echo "Unsupported system: $(uname -s). On Windows use install.ps1 (see the README)."; exit 1 ;;
  esac

  # Already inside a checkout? Then just use it.
  local here=""
  if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
    here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  fi

  if [ -n "$here" ] && [ -f "$here/$INSTALLER" ]; then
    DEST="$here"
    echo "Using existing folder: $DEST"
  else
    if [ -d "$DEST" ] && [ -n "$(ls -A "$DEST" 2>/dev/null)" ] && [ ! -f "$DEST/app/server.py" ]; then
      echo "$DEST already exists and doesn't look like OpenFIDS. Set OPENFIDS_DIR to another folder."
      exit 1
    fi
    local tmp; tmp="$(mktemp -d)"
    trap 'rm -rf "$tmp"' EXIT
    echo "Downloading OpenFIDS ($REF) ..."
    curl -fsSL "https://codeload.github.com/$REPO/tar.gz/$REF" -o "$tmp/src.tar.gz" \
      || { echo "Download failed. Check your connection, and that the repo is public."; exit 1; }
    mkdir -p "$tmp/x" "$DEST"
    tar -xzf "$tmp/src.tar.gz" -C "$tmp/x" --strip-components=1
    cp -R "$tmp/x/." "$DEST/"     # existing .venv is left alone, so re-running = update
    echo "Installed files to $DEST"
  fi

  cd "$DEST"
  chmod +x ./*.sh ./*.command 2>/dev/null || true

  # When run as "curl | bash", stdin is the script, so give the installer the real terminal for its prompts.
  if (exec </dev/tty) 2>/dev/null; then
    exec bash "./$INSTALLER" </dev/tty
  else
    exec bash "./$INSTALLER"
  fi
}

main "$@"
