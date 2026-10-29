# OpenFIDS

A flight information board that runs on your own computer. No accounts, no logins, nothing to sign up for.
It starts a small server on `127.0.0.1` (only your computer can reach it) and opens the board in your browser.
Out of the box it shows Cairns Airport, and it can be pointed at other airports (see Advanced).

- [Simple: install, use, uninstall](#simple)
- [Advanced: manual setup, feeds, customising](#advanced)

---

# Simple

## Install

**Linux and macOS.** Paste into a terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/Mandrusian/openfids/main/install.sh | bash
```

**Windows.** Paste into PowerShell:

```powershell
irm https://raw.githubusercontent.com/Mandrusian/openfids/main/install.ps1 | iex
```

This downloads OpenFIDS into a folder called `openfids` in your home folder, sets it up, and adds a shortcut.
If Python isn't installed, the installer offers to install it for you.

## Start it

Use the **OpenFIDS** shortcut:

| | Where to find it |
|---|---|
| Windows | Desktop and Start menu |
| macOS | `~/Applications/OpenFIDS.app` and a link on the Desktop |
| Linux | Your applications menu and the Desktop |

Clicking the shortcut again while it's running just reopens the page.

## Stop it

Click the power button at the bottom of the left menu.

## Update

Run the install command again. Your settings and data are kept.

## Uninstall

First stop OpenFIDS with the power button. Then paste the block for your system. These delete the app, the shortcuts and your saved data
(custom movements, feed login, settings files), so skip the last line of each block if you want to keep your data.

**Linux**

```bash
rm -rf ~/openfids
rm -f ~/.local/share/applications/openfids.desktop "$(xdg-user-dir DESKTOP 2>/dev/null || echo ~/Desktop)/OpenFIDS.desktop"
rm -rf ~/.local/share/openfids
```

**macOS**

```bash
rm -rf ~/openfids ~/Applications/OpenFIDS.app ~/Desktop/OpenFIDS
rm -rf ~/Library/Application\ Support/OpenFIDS
```

**Windows (PowerShell)**

```powershell
Remove-Item -Recurse -Force "$HOME\openfids"
Remove-Item -Force "$([Environment]::GetFolderPath('Desktop'))\OpenFIDS.lnk","$([Environment]::GetFolderPath('Programs'))\OpenFIDS.lnk" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\OpenFIDS"
```

Nothing is installed system-wide, so that's everything. (Python, if the installer added it, stays; remove it like any other program.)

## Using the board

- **Flight board.** Select Cairns (T1/T2) or Mackay (MTB), then browse arrivals, departures, or both. See ARR/DEP totals, codeshares, freight/charter labels, aircraft type/registration, scheduled/estimated/actual/block times, bay, gate, baggage carousel and public status, grouped by date. Search flight, codeshare, airline, place, registration, or aircraft name. Several words work, for example `qantas 738`.
  The chips switch between All, Arrivals, Departures, Military and Rare.
- **Board layout.** Comfortable is the default readable OpenFIDS layout, while Detailed reveals all 15 operational columns. Hover or keyboard-focus column headings for definitions. All flight times include the colon (e.g. `16:10` or `4:10 pm`).
- **More filters.** Filter by airline, aircraft, status and time window. A badge shows how many are active.
- **Early and delayed flights** get a coloured bubble on the right, such as "Delayed by 15 min".
- **Watchlist.** Click ★ next to a flight to follow it. You'll get a message (and an optional chime) when its status changes.
- **Statistics.** Counts and the busiest airlines, aircraft and destinations.
- **Add a movement.** Put your own flight on the board. It's stored on your computer only.
- **Export CSV** saves the current filtered board, including the new operational columns, to a spreadsheet file.
- **Settings.** Themes, accent colour, custom colours, upgraded Liquid Glass with adjustable depth (Subtle/Balanced/Deep), compact rows, motion, text size, a dedicated **12H / 24H** switch (flight board and clock), refresh rate and feed information.
- **Keyboard shortcuts.** `/` search, `b` board, `w` watchlist, `s` statistics, `n` add, `,` settings, `[` collapse menu, `Esc` close a panel.

## If something looks wrong

| You see | What to do |
|---|---|
| "Offline" or "Stale" in the left menu | Open **Settings → Feed** to see source freshness; check your connection or wait for NQA to update. |
| Aircraft or airline shows as "Operator XX" | The code isn't in the built-in list. See *Adding aircraft and airlines* under Advanced. |
| macOS says a file "can't be opened" | Right-click it, choose **Open**, then **Open** again. |
| Linux desktop icon shows a warning | Right-click it and choose **Allow Launching**. |
| Windows SmartScreen warning | Choose **More info**, then **Run anyway**. |
| Changed something and nothing happened | Reload the page with Ctrl+Shift+R (Cmd+Shift+R on macOS). |

## A note on AI

OpenFIDS was written with the help of an AI assistant (Claude, made by Anthropic), working from my instructions. This is a heads-up, and it doesn't change how you use the app.

- **There's no AI inside OpenFIDS.** The app doesn't call any AI service and doesn't send your searches, watchlist or settings anywhere.
- **What it does connect to:** the flight feed you've set up (Cairns Airport by default), Google Fonts for the typeface, and GitHub and PyPI when you install or update.
- **AI-written code can have mistakes.** Some parts, including the installers and shortcut scripts, haven't been tested on every operating system. If something breaks, please open an issue and include what you saw.
- **Read before you run.** As with any `curl | bash` command, you can read `install.sh` first. The link is in the Advanced section.

---

# Advanced

## Manual install

Use this if you'd rather not pipe a script into your shell. Download or clone the repo, then:

| | Install (once) | Make a shortcut | Start manually |
|---|---|---|---|
| **Windows** | double-click `install_windows.bat` | `shortcut_windows.bat` | `start_windows.bat` |
| **macOS** | double-click `install_macos.command` | `shortcut_macos.command` | `start_macos.command` |
| **Linux** | `./install_linux.sh` | `./shortcut_linux.sh` | `./start_linux.sh` |

```bash
git clone https://github.com/Mandrusian/openfids.git && cd openfids && ./install_linux.sh
```

The installer finds Python 3.9+, builds a private `.venv` inside the folder, and installs three small packages (fastapi, uvicorn, requests).
The shortcut scripts are separate so you can re-run them if you move the folder.

Quick-install options (environment variables, set them before `bash`):

```bash
curl -fsSL https://raw.githubusercontent.com/Mandrusian/openfids/main/install.sh | OPENFIDS_DIR=/some/folder OPENFIDS_REF=main bash
```

`OPENFIDS_DIR` changes the install folder (default `~/openfids`), and `OPENFIDS_REF` picks a branch, tag or commit.
To read the script first: `https://raw.githubusercontent.com/Mandrusian/openfids/main/install.sh`.

Optional native window instead of the browser: `.venv/bin/pip install pywebview`, then start with `.venv/bin/python app/launcher.py --window`.
Other launcher flags: `--no-open` serves without opening anything. The app uses port 8000, or the next free port up to 8019.

## Your data folder

| OS | Folder |
|---|---|
| Windows | `%APPDATA%\OpenFIDS` |
| macOS | `~/Library/Application Support/OpenFIDS` |
| Linux | `~/.local/share/openfids` |

Override it with the `OPENFIDS_DATA` environment variable. It holds everything you can customise:

| File | Purpose |
|---|---|
| `custom_flights.json` | Movements you add with the Add button (managed by the app) |
| `config.json` | Airport selection, feed settings and board title |
| `adapter.py` | Optional Python function that fetches flights from any source |
| `aircraft.json`, `airlines.json` | Extra aircraft and airline info, merged over the built-in lists |
| `openfids.log` | Log file |

Theme, colours and display settings are saved in your browser. `config.json` and `adapter.py` are re-read on every refresh,
so edits apply within a few seconds. Reload the page after changing `title`.

## Live feed (default: Cairns Airport)

By default OpenFIDS reads `https://flights.nqa.au/v1/flights`, the JSON endpoint used by the Cairns Airport flight board. **No login or API key is needed.**

The built-in NQA adapter maps arrivals/departures, flight number, origin/destination, scheduled and estimated times, public status, gate, stand, baggage carousel and aircraft registration to the existing OpenFIDS fields. The API contains Cairns (CNS) and Mackay (MKY); OpenFIDS loads both and initially displays **Cairns**. The new airport and terminal selectors switch views without a second request. The source's `public` flag does not necessarily mean a record is absent from its public-facing board: for example, the airport displays freight movements flagged `N`. Accordingly, the built-in feed includes those records by default.

To change the airport or include non-public records, use `config.json` in your OpenFIDS data directory:

```json
{ "airport": "CNS", "include_non_public": true }
```

Set `"airport": "MKY"` to make Mackay the initial selection (the UI offers CNS and MKY). The terminal controls automatically switch between Cairns **T1/T2** and Mackay **MTB**, and each airport remembers its own selection. Mackay's official board link is `https://flights.cairnsairport.com.au/#mky/both/MTB`. Set `"include_non_public": false` to hide records flagged `N`; this also hides some freight movements shown by the airport itself. These settings affect the built-in NQA source, not custom feeds or `adapter.py`.

Settings → Feed and the board header show source timestamps, stale state and the URL. OpenFIDS keeps the last fetched flights if the upstream request fails, and retries automatically. Note that the airport feed may lag the actual movement time.

Old `upstream_email` and `upstream_password` keys are **no longer used**. If you had configured them, you can remove them from your local `config.json`. The former login form and endpoints have been retired.
## Adding aircraft and airlines

The built-in lists are keyed by IATA and ICAO codes, case-insensitive (so `737`, `738`, `B738`, `QF` and `QFA` all work).
Add your own in the data folder. They're merged over the built-ins:

```json
{ "B38M": { "name": "Boeing 737 MAX 8", "desc": "Narrow-body twinjet.", "rare": false, "military": false } }
```
```json
{ "ANZ": { "name": "Air New Zealand", "desc": "Flag carrier of New Zealand.", "military": false } }
```

Put the first in `aircraft.json` and the second in `airlines.json`. `rare` and `military` drive the Rare and Military filters and the tags on the board.
Reload the page afterwards.

## Using a different flight board

There are three levels, from least to most work.

### 1. Rename the board

```json
{ "title": "Brisbane Airport FIDS" }
```

### 2. Any JSON feed, with only a config file

Most airport websites load their board from a JSON endpoint. To find it, open the airport's flight page, press F12,
open the **Network** tab, filter by **Fetch/XHR**, reload, and look for the request whose response is a list of flights.
Copy its URL. Then describe where the list is and what the fields are called:

```json
{
  "title": "Example Airport FIDS",
  "feed": {
    "url": "https://example.com/api/departures",
    "headers": { "Authorization": "Bearer YOUR_TOKEN" },
    "flights_path": "data.flights",
    "fields": {
      "airline": "carrier.icao",
      "flightNumber": "number",
      "portName": "destination.city",
      "portIATA": "destination.iata",
      "scheduled": "times.scheduled",
      "estimated": "times.estimated",
      "statusMsgPublic": "status",
      "acType": "aircraft.type",
      "acRego": "aircraft.registration",
      "vector": "=D"
    }
  }
}
```

- `flights_path` is a dotted path to the list (leave it out if the response itself is the list).
- Each value in `fields` is a dotted path into one flight. A value starting with `=` is a constant, so `"=D"` marks every row a departure.
- `vector` becomes `A` (arrival) or `D` (departure). Anything starting with A or D works.
- `scheduled` and `estimated` should be ISO text such as `2026-10-21T14:35:00`. The board uses both to work out "Delayed by" and "Early by".
- API keys go in the URL or in `headers`. They're stored in plain text in `config.json`, so keep that file private.

Fields the board understands: `vector`, `airline`, `flightNumber`, `portName`, `portIATA`, `terminal`, `scheduled`,
`estimated`, `statusMsgPublic`, `gate`, `stand`, `acType`, `acRego`, `id`. Missing ones are left blank.
Airline codes are matched as written, so if your feed uses 2-letter IATA codes (QF) rather than 3-letter ICAO codes (QFA),
the built-in list covers common ones, and `airlines.json` covers the rest.

### 3. Anything else: write a tiny adapter

For logins, HTML pages, separate arrivals and departures URLs, or APIs that need several calls, create `adapter.py` in
your data folder. It must define `fetch(session)` and return a list of flight dictionaries. `session` is a normal
`requests.Session`.

```python
def fetch(session):
    out = []
    for vector, url in (("A", "https://example.com/api/arrivals"),
                        ("D", "https://example.com/api/departures")):
        data = session.get(url, timeout=8).json()
        for row in data["flights"]:
            out.append({
                "vector": vector,
                "airline": row["airline_icao"],
                "flightNumber": row["number"],
                "portName": row["city"],
                "portIATA": row["iata"],
                "scheduled": row["scheduled"],
                "estimated": row.get("estimated"),
                "statusMsgPublic": row["status"],
                "gate": row.get("gate", ""),
                "acType": row.get("aircraft", ""),
                "acRego": row.get("rego", ""),
            })
    return out
```

If it raises an error, the board shows the message in the Offline notice. To scrape HTML, install a parser into the app's
environment, for example `.venv/bin/pip install beautifulsoup4`. An adapter is ordinary Python running with your own
permissions, so only use code you wrote or trust. If `adapter.py` exists it takes priority over `config.json`.

### Other sources worth trying
- The airport's own website board (the Network tab method above). Check the site's terms before scraping.
- Paid or free-tier flight APIs (aviationstack, FlightAware AeroAPI, AirLabs and similar). They usually need an API key, and
  their field names differ, so check their docs and map them in `fields`.
- ADS-B aggregators such as OpenSky show aircraft currently in the air near a location. That is spotting data, not a schedule.

### Testing a feed

With OpenFIDS running (the port is printed on start, normally 8000):

```bash
curl -s http://127.0.0.1:8000/api/flights | python3 -m json.tool | head -40
curl -s http://127.0.0.1:8000/api/status
```

`/api/status` shows the feed state and the last error message.

## Security notes

- The server only listens on `127.0.0.1` and rejects requests whose Host header isn't localhost.
- Stopping the app needs a custom header, so other websites can't trigger it.
- `adapter.py` runs as ordinary Python with your permissions.

## Website and embedded live demo

The OpenFIDS GitHub Pages website is generated from the static files in `docs/`:

- Website: https://mandrusian.github.io/openfids/
- Interactive preview: https://mandrusian.github.io/openfids/demo/

The embedded preview uses the **actual OpenFIDS interface** and the public `https://flights.nqa.au/v1/flights` JSON endpoint. It translates the NQA response to the same flight fields the desktop app uses; no account or proxy is needed. It relies on browser CORS access and on NQA being reachable, and does not fabricate flight information when the feed is unavailable.

The website demo is read-only; adding custom flights and stopping the local server are disabled. All desktop features remain in the installed app.

`scripts/build_pages.py` rebuilds the static demo UI from `app/index.html` and exports aircraft/airline lookups from `app/database.py`. The build also generates root `index.html` and `demo/index.html` entry points that reuse the assets in `docs/`, so both supported Pages folders work. Commit these generated entry points after changing the website. `.github/workflows/pages.yml` validates the website and checks that generated output is current; GitHub’s built-in Pages workflow handles publishing.

**Publishing setup:** GitHub repository Settings → Pages → Build and deployment → Source → **Deploy from a branch**, branch **main**, folder **/(root)** (or **/docs**). The project uses static branch publishing and does not need an additional Actions deployment or admin token.

Example embed:

```html
<iframe title="OpenFIDS live demo" src="https://mandrusian.github.io/openfids/demo/" style="width:100%;height:650px;border:0"></iframe>
```
