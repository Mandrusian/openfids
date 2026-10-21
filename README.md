# FreeFIDS (local edition)

Cairns Airport flight board that runs on your own computer. No accounts, no logins, nothing to sign up for.
It starts a small server on `127.0.0.1` (only your computer can reach it) and opens it in your browser.

## Install

Unzip the folder somewhere permanent (e.g. Documents), then:

| | Install (once) | Make a shortcut | Start manually |
|---|---|---|---|
| **Windows** | double-click `install_windows.bat` | `shortcut_windows.bat` | `start_windows.bat` |
| **macOS** | double-click `install_macos.command` | `shortcut_macos.command` | `start_macos.command` |
| **Linux** | `./install_linux.sh` | `./shortcut_linux.sh` | `./start_linux.sh` |

The installer finds Python 3.9+ (and offers to install it if missing), builds a private `.venv` inside the folder,
installs three small packages (fastapi, uvicorn, requests) and creates the shortcut for you.
The shortcut scripts are separate so you can re-run them if you move the folder.

- **Windows:** a `FreeFIDS` shortcut appears on the Desktop and in the Start menu (no console window).
- **macOS:** `~/Applications/FreeFIDS.app` plus a link on the Desktop.
- **Linux:** an entry in your applications menu plus a Desktop icon.

Stop the app with the ⏻ button in the top-right corner. Clicking the shortcut again while it is running just reopens the page.

### First-run notes
- **macOS:** if double-clicking says the file "can't be opened", right-click it, choose **Open**, then **Open** again
  (or run `xattr -dr com.apple.quarantine <folder>` in Terminal). If a script won't run, `chmod +x *.command`.
- **Linux:** if the Desktop icon shows a warning, right-click it and choose **Allow Launching**.
- **Windows:** if SmartScreen warns about the `.bat` files, choose **More info → Run anyway**.
- Optional native window instead of the browser: `.venv/bin/pip install pywebview`, then start with `--window`.

## Live feed (please read)

The board reads `https://flights.cairnsairport.com.au/flights/data`. The original project logged in to that site
with a hard-coded account. **That login is not included here**, so nobody else's password ships with the app.

- If the feed works without a login, you'll see **LIVE** in the header.
- If the airport site asks for a login, the header shows **OFFLINE** with a notice, and only movements you add yourself (➕) appear.
  If you have your own account, put it in `config.json` inside your data folder (below), or set the environment variables
  `FREEFIDS_UPSTREAM_EMAIL` and `FREEFIDS_UPSTREAM_PASSWORD`:

```json
{ "upstream_email": "you@example.com", "upstream_password": "your-password" }
```

## Where your stuff lives

| OS | Data folder |
|---|---|
| Windows | `%APPDATA%\FreeFIDS` |
| macOS | `~/Library/Application Support/FreeFIDS` |
| Linux | `~/.local/share/freefids` |

It holds `custom_flights.json`, the optional `config.json`, and `freefids.log`. Theme and display settings are saved in your browser.

## What changed from the original

Removed (they only make sense with shared accounts): sign-up/login, admin passwords and roles, chat, online roster,
profiles, notices, maintenance mode, troll mode. Kept: live board, search, Arrivals/Departures/Military/Rare filters,
aircraft & airline info tooltips, CSV export, themes, compact mode, audio chimes, refresh rate, and custom movements
(now open to the local user). Also fixed: flight data is HTML-escaped, and the server accepts only localhost requests.

## Uninstall
Delete the folder, the shortcut(s), and optionally the data folder above. Nothing is installed system-wide.
