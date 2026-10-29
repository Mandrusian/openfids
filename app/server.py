"""OpenFIDS local server.

Runs entirely on the user's own computer, bound to 127.0.0.1. There are no
accounts or logins: whoever is sitting at the machine is the user.
"""
import json
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import requests
from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from database import AIRCRAFT_DB, AIRLINE_DB
from nqa import FEED_URL, extract_flights

APP_DIR = Path(__file__).resolve().parent


def get_data_dir() -> Path:
    """Per-user folder for settings and custom flights (survives updates)."""
    override = os.environ.get("OPENFIDS_DATA")
    if override:
        path = Path(override).expanduser()
    elif sys.platform.startswith("win"):
        path = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "OpenFIDS"
    elif sys.platform == "darwin":
        path = Path.home() / "Library" / "Application Support" / "OpenFIDS"
    else:
        path = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "openfids"
    path.mkdir(parents=True, exist_ok=True)
    return path


DATA_DIR = get_data_dir()
CUSTOM_FLIGHTS_FILE = DATA_DIR / "custom_flights.json"
CONFIG_FILE = DATA_DIR / "config.json"
_file_lock = threading.Lock()

app = FastAPI(title="OpenFIDS", docs_url=None, redoc_url=None, openapi_url=None)

ALLOWED_HOSTS = {"127.0.0.1", "localhost", "[::1]"}


@app.middleware("http")
async def local_only(request: Request, call_next):
    """Reject requests whose Host header isn't localhost (DNS-rebinding guard)."""
    raw = request.headers.get("host") or ""
    host = "[::1]" if raw.startswith("[") else raw.rsplit(":", 1)[0]
    if host not in ALLOWED_HOSTS:
        return JSONResponse({"error": "local access only"}, status_code=403)
    return await call_next(request)


# --------------------------------------------------------------------------
# Custom (locally added) flights
# --------------------------------------------------------------------------
def load_custom_flights() -> list:
    with _file_lock:
        try:
            data = json.loads(CUSTOM_FLIGHTS_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []


def save_custom_flights(flights: list) -> None:
    with _file_lock:
        CUSTOM_FLIGHTS_FILE.write_text(json.dumps(flights, indent=2), encoding="utf-8")


def clean(value, default="", limit=60) -> str:
    return str(value if value is not None else default).strip()[:limit] or default


# --------------------------------------------------------------------------
# Live feed from Cairns Airport
# --------------------------------------------------------------------------

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (OpenFIDS local app)"})

feed = {"ok": False, "message": "Connecting to NQA...", "updated": None, "source": FEED_URL, "stale": False}
_feed_lock = threading.Lock()
_cache = {"time": 0.0, "flights": []}


def _set_feed(ok: bool, message: str):
    feed["ok"] = ok
    feed["message"] = message
    if ok:
        feed["updated"] = datetime.now().strftime("%H:%M:%S")


# ---- pluggable feeds (see README: "Using a different flight board") ----
ADAPTER_FILE = DATA_DIR / "adapter.py"


def load_config() -> dict:
    try:
        cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return cfg if isinstance(cfg, dict) else {}
    except Exception:
        return {}


def load_adapter():
    # Optional adapter.py in the data folder must define fetch(session) -> list of flight dicts.
    if not ADAPTER_FILE.exists():
        return None
    import importlib.util
    spec = importlib.util.spec_from_file_location("openfids_adapter", ADAPTER_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fn = getattr(module, "fetch", None)
    if not callable(fn):
        raise RuntimeError("adapter.py must define fetch(session)")
    return fn


def dig(data, path):
    for part in str(path).split("."):
        if not part:
            continue
        if isinstance(data, dict):
            data = data.get(part)
        elif isinstance(data, list) and part.isdigit() and int(part) < len(data):
            data = data[int(part)]
        else:
            return None
    return data


def normalise(raw, mapping):
    if not isinstance(raw, dict):
        return None
    out = dict(raw)
    for ours, theirs in (mapping or {}).items():
        if isinstance(theirs, str) and theirs.startswith("="):
            out[ours] = theirs[1:]          # "=D" means the constant "D"
            continue
        value = dig(raw, theirs)
        if value is not None:
            out[ours] = value
    vector = str(out.get("vector", "")).strip().upper()
    if vector:
        out["vector"] = "A" if vector.startswith("A") else "D"
    return out


def extra_db(name: str) -> dict:
    try:
        data = json.loads((DATA_DIR / name).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _try_fetch():
    """Fetch a user adapter, configured feed, or default NQA feed."""
    try:
        adapter = load_adapter()
    except Exception as exc:
        return None, f"adapter failed to load: {exc}", {}
    if adapter:
        try:
            flights = adapter(session)
        except requests.RequestException:
            raise
        except Exception as exc:
            return None, f"adapter error: {exc}", {}
        return [f for f in (flights or []) if isinstance(f, dict)], None, {"source": "Local adapter", "stale": False}

    config = load_config()
    cfg = config.get("feed") or {}
    if not isinstance(cfg, dict):
        return None, "feed configuration must be an object", {}
    custom = bool(cfg.get("url"))
    url = cfg.get("url") or FEED_URL
    resp = session.get(url, timeout=8, headers=cfg.get("headers") or None)
    if resp.status_code != 200:
        return None, f"http {resp.status_code}", {"source": url}
    try:
        data = resp.json()
    except ValueError:
        return None, "response was not JSON", {"source": url}
    if custom:
        items = dig(data, cfg["flights_path"]) if cfg.get("flights_path") else data
        if not isinstance(items, list):
            return None, "flights_path did not point at a list", {"source": url}
        flights = [f for f in (normalise(i, cfg.get("fields")) for i in items) if f]
        return flights, None, {"source": url, "stale": False, "count": len(flights)}
    try:
        flights, meta = extract_flights(
            data, airport="ALL",
            include_non_public=config.get("include_non_public", True) is True,
        )
    except ValueError as exc:
        return None, f"invalid NQA feed: {exc}", {"source": url}
    meta["source"] = url
    return flights, None, meta


def fetch_live_flights() -> list:
    with _feed_lock:
        if time.time() - _cache["time"] < 4:
            return _cache["flights"]
        try:
            flights, problem, metadata = _try_fetch()
            if problem:
                feed.update(metadata)
                feed["stale"] = True
                _set_feed(False, f"Airport feed unavailable ({problem}). Retrying automatically.")
                return _cache["flights"]
            _cache.update(time=time.time(), flights=flights)
            feed.update(metadata)
            if feed.get("stale"):
                reasons = ", ".join(map(str, feed.get("staleReasons") or []))
                _set_feed(False, f"NQA data is stale{': ' + reasons if reasons else ''}.")
            else:
                _set_feed(True, "Live")
            return flights
        except requests.RequestException:
            feed["stale"] = True
            _set_feed(False, "Can't reach the airport feed. Showing last received flights, if available.")
            return _cache["flights"]


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index():
    try:
        return (APP_DIR / "index.html").read_text(encoding="utf-8")
    except FileNotFoundError:
        return HTMLResponse("<h1>index.html not found</h1>", status_code=500)


@app.get("/api/status")
def status():
    return {"app": "openfids", "data_dir": str(DATA_DIR),
            "title": load_config().get("title", "Cairns Airport FIDS"),
            "defaultAirport": load_config().get("airport", "CNS"), "feed": feed}


@app.get("/api/database")
def database():
    return {"aircraft": {**AIRCRAFT_DB, **extra_db("aircraft.json")},
            "airlines": {**AIRLINE_DB, **extra_db("airlines.json")}}


@app.get("/api/flights")
def flights():
    live = fetch_live_flights()
    return {"flights": load_custom_flights() + live, "feed": feed}


@app.get("/api/custom-flights")
def list_custom_flights():
    return {"flights": load_custom_flights()}


@app.post("/api/custom-flights")
def add_custom_flight(data: dict = Body(...)):
    airline = clean(data.get("airline"), "VIP", 8).upper()
    number = clean(data.get("flightNumber"), "1", 8)
    vector = "D" if data.get("vector") == "D" else "A"
    scheduled = clean(data.get("scheduled"), "", 40)
    try:
        datetime.fromisoformat(scheduled)
    except ValueError:
        scheduled = datetime.now().replace(microsecond=0).isoformat()
    airport = clean(data.get("airport"), "CNS", 3).upper()
    if airport not in ("CNS", "MKY"):
        airport = "CNS"
    flight = {
        "id": f"CF-{int(time.time() * 1000)}",
        "airport": airport,
        "vector": vector,
        "airline": airline,
        "flightNumber": number,
        "portIATA": clean(data.get("portIATA"), "CNS", 4).upper(),
        "portName": clean(data.get("portName"), "Cairns Local Operational"),
        "terminal": clean(data.get("terminal"), "T1", 8),
        "scheduled": scheduled,
        "statusMsgPublic": clean(data.get("status"), "Special Ops"),
        "gate": clean(data.get("gate"), "Bay 1", 12),
        "acType": clean(data.get("acType"), "GLF6", 6).upper(),
        "acRego": clean(data.get("acRego"), "N1VIP", 12).upper(),
        "custom": True,
    }
    flights_list = load_custom_flights()
    flights_list.append(flight)
    save_custom_flights(flights_list)
    return {"flights": flights_list}


@app.delete("/api/custom-flights/{flight_id}")
def delete_custom_flight(flight_id: str):
    flights_list = [f for f in load_custom_flights() if f.get("id") != flight_id]
    save_custom_flights(flights_list)
    return {"flights": flights_list}


@app.post("/api/quit")
def quit_app(request: Request):
    # Custom header forces a CORS preflight, so other websites can't trigger this.
    if request.headers.get("x-openfids") != "1":
        raise HTTPException(status_code=403, detail="forbidden")
    threading.Timer(0.4, lambda: os._exit(0)).start()
    return {"status": "stopping"}
