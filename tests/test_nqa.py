"""Tests for the built-in NQA adapter (offline fixture, no live API calls)."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from nqa import FEED_URL, convert_flight, extract_flights
import server


def sample(airport="CNS", direction="A", public="P"):
    return {
        "id": "248750", "airport": airport, "direction": direction, "public": public,
        "flight": "QF2354", "airline": "QF", "flightNumber": "2354",
        "port": {"iata": "TSV", "name": "Townsville"}, "terminal": "T2",
        "scheduled": "2026-10-29T14:00:00+10:00",
        "estimated": "2026-10-29T13:36:00+10:00",
        "actual": "2026-10-29T13:35:44+10:00",
        "onBlock": "2026-10-29T13:38:33+10:00",
        "status": {"public": "Landed", "staff": "On Block"},
        "carousel": "D02", "gate": "D16", "stand": "16",
        "aircraft": {"type": "DH4", "registration": "VH84H"},
        "codeShares": ["NZ7169"],
    }


class NQATests(unittest.TestCase):
    def test_translation(self):
        f = convert_flight(sample())
        self.assertEqual(f["id"], "NQA-CNS-248750")
        self.assertEqual(f["vector"], "A")
        self.assertEqual((f["airline"], f["flightNumber"]), ("QF", "2354"))
        self.assertEqual((f["portName"], f["portIATA"]), ("Townsville", "TSV"))
        self.assertEqual(f["statusMsgPublic"], "Landed")
        self.assertEqual((f["acType"], f["acRego"]), ("DH4", "VH84H"))
        self.assertEqual(f["actual"], "2026-10-29T13:35:44+10:00")
        self.assertEqual((f["gate"], f["carousel"]), ("D16", "D02"))
        self.assertNotIn("staff", f)

    def test_departure_and_missing_fields(self):
        self.assertEqual(convert_flight(sample(direction="D"))["vector"], "D")
        f = convert_flight({"airport": "CNS", "direction": "D",
                            "scheduled": "2026-10-29T15:00:00+10:00",
                            "airline": "VA", "flight": "VA783"})
        self.assertEqual(f["flightNumber"], "783")
        self.assertEqual(f["statusMsgPublic"], "")

    def test_airport_public_filter_and_metadata(self):
        body = {"flights": [sample(), sample(airport="MKY"), sample(public="N")],
                "stale": False, "ageSeconds": 376}
        fs, meta = extract_flights(body)
        self.assertEqual((len(fs), meta["count"], meta["ageSeconds"]), (2, 2, 376))
        self.assertEqual(len(extract_flights(body, airport="ALL")[0]), 3)
        self.assertEqual(len(extract_flights(body, include_non_public=False)[0]), 1)

    def test_stale_and_invalid(self):
        self.assertTrue(extract_flights({"flights": [], "stale": True})[1]["stale"])
        for body in ({}, [], {"flights": {}}):
            with self.assertRaises(ValueError):
                extract_flights(body)
        with self.assertRaises(ValueError):
            extract_flights({"flights": []}, airport="XYZ")

    def test_default_server_fetch(self):
        class Response:
            status_code = 200
            def json(self):
                return {"flights": [sample()], "stale": False}
        with patch.object(server, "load_config", return_value={}), \
             patch.object(server, "load_adapter", return_value=None), \
             patch.object(server.session, "get", return_value=Response()) as get:
            flights, problem, metadata = server._try_fetch()
        self.assertIsNone(problem)
        self.assertEqual(flights[0]["statusMsgPublic"], "Landed")
        self.assertEqual(metadata["source"], FEED_URL)
        self.assertEqual(get.call_args.args[0], FEED_URL)


    def test_server_returns_both_airports_by_default(self):
        class Response:
            status_code = 200
            def json(self):
                return {"flights": [sample(), sample(airport="MKY"), sample(public="N")],
                        "stale": False}
        with patch.object(server, "load_config", return_value={}), \
             patch.object(server, "load_adapter", return_value=None), \
             patch.object(server.session, "get", return_value=Response()):
            flights, problem, metadata = server._try_fetch()
        self.assertIsNone(problem)
        self.assertEqual(len(flights), 3)
        self.assertEqual(set(f["airport"] for f in flights), {"CNS", "MKY"})
        self.assertEqual(metadata["count"], 3)

    def test_explicit_opt_out_non_public(self):
        class Response:
            status_code = 200
            def json(self):
                return {"flights": [sample(), sample(public="N")], "stale": False}
        with patch.object(server, "load_config", return_value={"include_non_public": False}), \
             patch.object(server, "load_adapter", return_value=None), \
             patch.object(server.session, "get", return_value=Response()):
            flights, problem, _ = server._try_fetch()
        self.assertIsNone(problem)
        self.assertEqual(len(flights), 1)

    def test_custom_feed_override(self):
        class Response:
            status_code = 200
            def json(self):
                return {"data": [{"carrier": "VA", "number": "123"}]}
        cfg = {"feed": {"url": "https://example.org/flights",
                        "flights_path": "data",
                        "fields": {"airline": "carrier", "flightNumber": "number", "vector": "=D"}}}
        with patch.object(server, "load_config", return_value=cfg), \
             patch.object(server, "load_adapter", return_value=None), \
             patch.object(server.session, "get", return_value=Response()):
            flights, problem, _ = server._try_fetch()
        self.assertIsNone(problem)
        self.assertEqual((flights[0]["airline"], flights[0]["vector"]), ("VA", "D"))


if __name__ == "__main__":
    unittest.main()
