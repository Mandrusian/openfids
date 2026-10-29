"""Low-cost UI regression assertions (node --check is run separately in CI)."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

PAGE = Path(__file__).resolve().parents[1] / "app" / "index.html"


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.duplicates = set()
    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k == "id":
                if v in self.ids:
                    self.duplicates.add(v)
                self.ids.add(v)


class BoardTests(unittest.TestCase):
    def test_controls_and_columns(self):
        text = PAGE.read_text(encoding="utf-8")
        p = Elements()
        p.feed(text)
        self.assertFalse(p.duplicates, p.duplicates)
        for name in ("airportPick", "terminalPick", "boardSummary",
                     "totalCount", "arrCount", "depCount", "sourceAsOf",
                     "rows", "refreshNow", "cfAirport", "feedDetails"):
            self.assertIn(name, p.ids)
        for label in ("From / To", "Sched", "Est", "Act", "Block",
                      "Bay", "Gate", "Car", "Status"):
            self.assertIn(label, text)
        self.assertIn("codeShares", text)
        self.assertIn("offBlock", text)
        self.assertIn("flightType", text)
        self.assertIn("airportScope()", text)
        self.assertIn("MKY: ['MTB']", text)
        self.assertIn("AIRPORT_TERMINALS[S.airport]", text)
        self.assertIn("S.terminalSelections[S.airport]", text)
        self.assertIn("terminalPick.dataset.airport !== S.airport", text)
        self.assertIn("Mackay Airport FIDS", text)

    def test_legacy_cairns_terminal_settings_migrate(self):
        text = PAGE.read_text(encoding="utf-8")
        self.assertIn("savedSelections.CNS ?? savedState.terminals", text)
        self.assertIn("savedSelections.MKY", text)
        self.assertIn("delete S.terminals", text)


if __name__ == "__main__":
    unittest.main()
