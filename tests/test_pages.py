"""Static Pages and embedded OpenFIDS demo regression tests."""
import unittest
import sys
from pathlib import Path
from html.parser import HTMLParser

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_pages import build

class IDs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.names=set()
        self.dupes=set()
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key=='id':
                if value in self.names:self.dupes.add(value)
                self.names.add(value)

class PagesTests(unittest.TestCase):
    def test_site(self):
        build()
        html=(ROOT/'docs/index.html').read_text(encoding='utf-8')
        parser=IDs();parser.feed(html)
        self.assertFalse(parser.dupes)
        for name in ('demoFrame','demoStatus','unixCmd','winCmd'):self.assertIn(name,parser.names)
        self.assertIn('src="./demo/"',html)
        demo=(ROOT/'docs/demo/index.html').read_text(encoding='utf-8')
        self.assertIn('<script src="./shim.js"></script>',demo)
        self.assertIn('id="flightTable"',demo)
        self.assertIn('id="airportPick"',demo)
        self.assertIn('id="timeFormat"',demo)
    def test_demo_uses_own_preferences(self):
        build()
        demo=(ROOT/'docs/demo/index.html').read_text(encoding='utf-8')
        self.assertIn("const LS = 'openfids.demo.v1';",demo)
        self.assertNotIn("const LS = 'openfids.v2';",demo)

    def test_live_source_and_read_only(self):
        import json
        lookup=json.loads((ROOT/'docs/demo/database.json').read_text(encoding='utf-8'))
        self.assertIn('QF',lookup['airlines'])
        self.assertIn('738',lookup['aircraft'])
        shim=(ROOT/'docs/demo/shim.js').read_text(encoding='utf-8')
        self.assertIn('https://flights.nqa.au/v1/flights',shim)
        self.assertIn('Disabled in read-only demo',shim)
        self.assertIn('cache?.flights||[]',shim)

if __name__=='__main__':
    unittest.main()
