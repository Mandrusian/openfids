# OpenFIDS

A flight information board that runs on your own computer. No accounts, no logins, nothing to sign up for.
It starts a small server on `127.0.0.1` (only your computer can reach it) and opens the board in your browser.
Out of the box it shows Cairns Airport, and it can be pointed at other airports (see below).

## Install

Unzip or clone the folder somewhere permanent (e.g. Documents), then:

| | Install (once) | Make a shortcut | Start manually |
|---|---|---|---|
| **Windows** | double-click `install_windows.bat` | `shortcut_windows.bat` | `start_windows.bat` |
| **macOS** | double-click `install_macos.command` | `shortcut_macos.command` | `start_macos.command` |
| **Linux** | `./install_linux.sh` | `./shortcut_linux.sh` | `./start_linux.sh` |

The installer finds Python 3.9+ (and offers to install it if missing), builds a private `.venv` inside the folder,
installs three small packages (fastapi, uvicorn, requests) and creates the shortcut. The shortcut scripts are separate
so you can re-run them if you move the folder.

- **Windows:** an `OpenFIDS` shortcut on the Desktop and in the Start menu (no console window).
- **macOS:** `~/Applications/OpenFIDS.app` plus a link on the Desktop.
- **Linux:** an applications-menu entry plus a Desktop icon.

Stop the app with the power button in the top-right corner. Clicking the shortcut again while it runs just reopens the page.

### First-run notes
- **macOS:** if double-clicking says the file can't be opened, right-click it, choose **Open**, then **Open** again
  (or run `xattr -dr com.apple.quarantine <folder>`). If a script won't run: `chmod +x *.command`.
- **Linux:** if the Desktop icon shows a warning, right-click it and choose **Allow Launching**.
- **Windows:** if SmartScreen warns about the `.bat` files, choose **More info, then Run anyway**.
- Optional native window instead of the browser: `.venv/bin/pip install pywebview`, then start with `--window`.

## Your data folder

| OS | Folder |
|---|---|
| Windows | `%APPDATA%\OpenFIDS` |
| macOS | `~/Library/Application Support/OpenFIDS` |
| Linux | `~/.local/share/openfids` |

Override it with the `OPENFIDS_DATA` environment variable. It holds everything you can customise:

| File | Purpose |
|---|---|
| `custom_flights.json` | Movements you add with the plus button (managed by the app) |
| `config.json` | Feed settings, board title, optional login (see below) |
| `adapter.py` | Optional Python function that fetches flights from any source |
| `aircraft.json`, `airlines.json` | Extra aircraft and airline info, merged over the built-in lists |
| `openfids.log` | Log file |

Theme and display settings are saved in your browser. `config.json` and `adapter.py` are re-read on every refresh,
so edits apply within a few seconds. Reload the page after changing `title`.

## Live feed (default: Cairns Airport)

By default the board reads `https://flights.cairnsairport.com.au/flights/data`.

- If it works without a login, the header shows **LIVE**.
- If the airport site asks for a login, the header shows **OFFLINE** with a notice and only movements you add yourself appear.
  If you have your own account, add it to `config.json`, or set `OPENFIDS_UPSTREAM_EMAIL` and `OPENFIDS_UPSTREAM_PASSWORD`:

```json
{ "upstream_email": "you@example.com", "upstream_password": "your-password" }
```

No credentials are bundled with OpenFIDS.

## Using a different flight board

There are three levels, from least to most work.

### 1. Rename the board and add your own aircraft/airline info

```json
{ "title": "Brisbane Airport FIDS" }
```

Tooltips and the Military/Rare filters use `aircraft.json` and `airlines.json`, keyed by code. Codes you don't define show as
`Operator [XX]` / `Aircraft [XXX]`. Entries use the same shape as the built-in lists:

```json
{ "B38M": { "name": "Boeing 737 MAX 8", "desc": "Narrow-body twinjet.", "rare": false, "military": false } }
```
```json
{ "ANZ": { "name": "Air New Zealand", "desc": "Flag carrier of New Zealand.", "military": false } }
```

### 2. Any JSON feed, with only a config file

Most airport websites load their board from a JSON endpoint. To find it: open the airport's flight page, press F12,
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
- `scheduled` and `estimated` should be ISO text such as `2026-10-21T14:35:00`.
- API keys go in the URL or in `headers`. Keys are stored in plain text in `config.json`, so keep that file private.

Fields the board understands: `vector`, `airline`, `flightNumber`, `portName`, `portIATA`, `terminal`, `scheduled`,
`estimated`, `statusMsgPublic`, `gate`, `stand`, `acType`, `acRego`, `id`. Missing ones are simply left blank.
Airline codes are matched against `airlines.json` as written, so if your feed uses 2-letter IATA codes (QF) rather than
3-letter ICAO codes (QFA), add those to `airlines.json`.

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
                "statusMsgPublic": row["status"],
                "gate": row.get("gate", ""),
                "acType": row.get("aircraft", ""),
                "acRego": row.get("rego", ""),
            })
    return out
```

If it raises an error, the board shows the message in the OFFLINE banner. To scrape HTML, install a parser into the app's
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

## Uninstall

Delete the folder, the shortcut(s), and optionally the data folder above. Nothing is installed system-wide.
