"""OpenFIDS local server.

Runs entirely on the user's own computer, bound to 127.0.0.1. There are no
accounts or logins: whoever is sitting at the machine is the user.
"""
import json
import os
import re
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import requests
from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from database import AIRCRAFT_DB, AIRLINE_DB

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
BASE_URL = "https://flights.cairnsairport.com.au"
FEED_URL = BASE_URL + "/flights/data"
LOGIN_URL = BASE_URL + "/login"

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (OpenFIDS local app)"})

feed = {"ok": False, "message": "Connecting to Cairns Airport...", "updated": None}
_feed_lock = threading.Lock()
_cache = {"time": 0.0, "flights": []}
_login_retry_after = 0.0


def upstream_credentials():
    """Optional login for the airport site, supplied by the user themselves.

    Nothing is bundled with the app. Set OPENFIDS_UPSTREAM_EMAIL and
    OPENFIDS_UPSTREAM_PASSWORD, or put {"upstream_email": "...",
    "upstream_password": "..."} in config.json inside the data folder.
    """
    email = os.environ.get("OPENFIDS_UPSTREAM_EMAIL", "")
    password = os.environ.get("OPENFIDS_UPSTREAM_PASSWORD", "")
    if not (email and password):
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            email = cfg.get("upstream_email", "")
            password = cfg.get("upstream_password", "")
        except Exception:
            pass
    return (email, password) if email and password else None


def upstream_login(email: str, password: str) -> bool:
    try:
        page = session.get(LOGIN_URL, timeout=8)
        match = re.search(r'name=["\']_token["\'][^>]*value=["\']([^"\']+)', page.text) or \
            re.search(r'value=["\']([^"\']+)["\'][^>]*name=["\']_token["\']', page.text)
        token = match.group(1) if match else ""
        headers = {"Referer": LOGIN_URL}
        xsrf = session.cookies.get("XSRF-TOKEN")
        if xsrf:
            headers["X-XSRF-TOKEN"] = xsrf
        resp = session.post(LOGIN_URL, data={"_token": token, "email": email, "password": password},
                            headers=headers, timeout=8)
        return resp.status_code in (200, 302)
    except requests.RequestException:
        return False


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
    try:
        adapter = load_adapter()
    except Exception as exc:
        return None, f"adapter failed to load: {exc}"
    if adapter:
        try:
            flights = adapter(session)
        except requests.RequestException:
            raise
        except Exception as exc:
            return None, f"adapter error: {exc}"
        return [f for f in (flights or []) if isinstance(f, dict)], None

    cfg = load_config().get("feed") or {}
    custom = bool(cfg.get("url"))
    resp = session.get(cfg.get("url") or FEED_URL, timeout=8, headers=cfg.get("headers") or None)
    if not custom and ("login" in resp.url or resp.status_code in (401, 403, 419)):
        return None, "login"
    if resp.status_code != 200:
        return None, f"http {resp.status_code}"
    try:
        data = resp.json()
    except ValueError:
        return None, ("response was not JSON" if custom else "login")
    if custom:
        items = dig(data, cfg["flights_path"]) if cfg.get("flights_path") else data
        if not isinstance(items, list):
            return None, "flights_path did not point at a list"
        flights = [f for f in (normalise(i, cfg.get("fields")) for i in items) if f]
    else:
        flights = data.get("flights", []) if isinstance(data, dict) else []
    return flights, None


def fetch_live_flights() -> list:
    global _login_retry_after
    with _feed_lock:
        if time.time() - _cache["time"] < 4:
            return _cache["flights"]
        try:
            flights, problem = _try_fetch()
            if problem == "login":
                creds = upstream_credentials()
                if not creds:
                    _set_feed(False, "The airport's flight feed asked for a login and none is configured. "
                                     "Only flights you add yourself are shown. See the README, \"Live feed\".")
                    return []
                if time.time() < _login_retry_after:
                    return _cache["flights"]
                if upstream_login(*creds):
                    flights, problem = _try_fetch()
                else:
                    _login_retry_after = time.time() + 60
                    _set_feed(False, "Login to the airport feed failed. Check the credentials in config.json.")
                    return []
            if problem:
                _set_feed(False, f"Airport feed unavailable ({problem}). Retrying automatically.")
                return _cache["flights"]
            _cache.update(time=time.time(), flights=flights)
            _set_feed(True, "Live")
            return flights
        except requests.RequestException:
            _set_feed(False, "Can't reach the airport feed. Check your internet connection.")
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
            "title": load_config().get("title", "Cairns Airport FIDS"), "feed": feed}


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
    flight = {
        "id": f"CF-{int(time.time() * 1000)}",
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


@app.get("/api/credentials")
def get_credentials():
    cfg = load_config()
    return {"email": cfg.get("upstream_email", ""),
            "has_password": bool(cfg.get("upstream_password")),
            "from_env": bool(os.environ.get("OPENFIDS_UPSTREAM_EMAIL"))}


def _write_config(cfg: dict) -> None:
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    try:
        os.chmod(CONFIG_FILE, 0o600)   # owner-only (no effect on Windows)
    except OSError:
        pass


def _reset_feed_state() -> None:
    global _login_retry_after
    _login_retry_after = 0.0
    _cache["time"] = 0.0
    session.cookies.clear()


@app.post("/api/credentials")
def set_credentials(request: Request, data: dict = Body(...)):
    if request.headers.get("x-openfids") != "1":
        raise HTTPException(status_code=403, detail="forbidden")
    cfg = load_config()
    cfg["upstream_email"] = clean(data.get("email"), "", 200)
    password = str(data.get("password") or "")
    if password:                       # blank = keep the saved password
        cfg["upstream_password"] = password[:200]
    _write_config(cfg)
    _reset_feed_state()
    fetch_live_flights()               # test it right away
    return {"feed": feed}


@app.delete("/api/credentials")
def clear_credentials(request: Request):
    if request.headers.get("x-openfids") != "1":
        raise HTTPException(status_code=403, detail="forbidden")
    cfg = load_config()
    cfg.pop("upstream_email", None)
    cfg.pop("upstream_password", None)
    _write_config(cfg)
    _reset_feed_state()
    fetch_live_flights()
    return {"feed": feed}


@app.post("/api/quit")
def quit_app(request: Request):
    # Custom header forces a CORS preflight, so other websites can't trigger this.
    if request.headers.get("x-openfids") != "1":
        raise HTTPException(status_code=403, detail="forbidden")
    threading.Timer(0.4, lambda: os._exit(0)).start()
    return {"status": "stopping"}
