"""Unit tests for the local OpenFIDS server routes, guards and caching."""
import asyncio
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from starlette.requests import Request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
import server


def make_request(host: str, headers: dict | None = None) -> Request:
    raw_headers = [(b"host", host.encode("ascii"))]
    for k, v in (headers or {}).items():
        raw_headers.append((k.lower().encode("ascii"), v.encode("ascii")))
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/status",
        "headers": raw_headers,
        "query_string": b"",
        "client": ("127.0.0.1", 12345),
        "server": ("127.0.0.1", 8000),
        "scheme": "http",
    }
    return Request(scope)


class ServerTests(unittest.TestCase):
    def test_local_only_allows_localhost_and_rejects_external_host(self):
        async def ok_next(_request):
            return server.JSONResponse({"ok": True})

        for host in ("127.0.0.1:8000", "localhost:8000", "[::1]:8000"):
            resp = asyncio.run(server.local_only(make_request(host), ok_next))
            self.assertEqual(resp.status_code, 200, host)

        for bad_host in ("evil.example", "192.168.1.50:8000", ""):
            resp = asyncio.run(server.local_only(make_request(bad_host), ok_next))
            self.assertEqual(resp.status_code, 403, bad_host)

    def test_quit_requires_custom_header(self):
        with self.assertRaises(HTTPException) as ctx:
            server.quit_app(make_request("127.0.0.1:8000"))
        self.assertEqual(ctx.exception.status_code, 403)

        with patch.object(server.threading, "Timer") as timer_cls:
            res = server.quit_app(make_request("127.0.0.1:8000", {"X-OpenFIDS": "1"}))
        self.assertEqual(res, {"status": "stopping"})
        timer_cls.return_value.start.assert_called_once()

    def test_dig_and_normalise(self):
        raw = {"carrier": {"iata": "QF"}, "legs": [{"port": "SYD"}], "dir": "arriving"}
        self.assertEqual(server.dig(raw, "legs.0.port"), "SYD")
        self.assertIsNone(server.dig(raw, "legs.5.port"))
        norm = server.normalise(raw, {"airline": "carrier.iata", "portIATA": "legs.0.port", "vector": "dir"})
        self.assertEqual(norm["airline"], "QF")
        self.assertEqual(norm["portIATA"], "SYD")
        self.assertEqual(norm["vector"], "A")
        self.assertEqual(server.normalise(raw, {"vector": "=D"})["vector"], "D")
        self.assertIsNone(server.normalise("not-a-dict", {}))

    def test_fetch_live_flights_caches_and_preserves_on_error(self):
        orig_cache = dict(server._cache)
        orig_feed = dict(server.feed)
        try:
            server._cache.update(time=0.0, flights=[])
            sample_flights = [{"id": "NQA-CNS-1", "airport": "CNS"}]
            with patch.object(server, "_try_fetch", return_value=(sample_flights, None, {"source": "test", "stale": False})):
                first = server.fetch_live_flights()
            self.assertEqual(first, sample_flights)
            self.assertTrue(server.feed["ok"])

            # Within 4s cache window, returns cached flights without calling _try_fetch.
            with patch.object(server, "_try_fetch", side_effect=AssertionError("should use cache")):
                cached = server.fetch_live_flights()
            self.assertEqual(cached, sample_flights)

            # Force expiry and simulate network error: cached flights must survive.
            server._cache["time"] = 0.0
            with patch.object(server, "_try_fetch", side_effect=server.requests.RequestException("down")):
                fallback = server.fetch_live_flights()
            self.assertEqual(fallback, sample_flights)
            self.assertFalse(server.feed["ok"])
            self.assertTrue(server.feed["stale"])
        finally:
            server._cache.clear()
            server._cache.update(orig_cache)
            server.feed.clear()
            server.feed.update(orig_feed)

    def test_custom_flights_crud_and_unique_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            cf_path = Path(tmp) / "custom_flights.json"
            with patch.object(server, "CUSTOM_FLIGHTS_FILE", cf_path), \
                 patch.object(server.time, "time", return_value=1700000000.123):
                r1 = server.add_custom_flight({"airline": "QF", "flightNumber": "1", "vector": "A"})
                r2 = server.add_custom_flight({"airline": "VA", "flightNumber": "2", "vector": "D"})
                ids = [f["id"] for f in r2["flights"]]
                self.assertEqual(len(ids), 2)
                self.assertEqual(len(set(ids)), 2)

                r3 = server.delete_custom_flight(ids[0])
                self.assertEqual([f["id"] for f in r3["flights"]], [ids[1]])
                self.assertEqual(r1["flights"][0]["id"], ids[0])


if __name__ == "__main__":
    unittest.main()
