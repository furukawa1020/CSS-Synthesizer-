"""Fragment targets and displayed major ticks must identify the same values."""
from html.parser import HTMLParser
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.build import ROOT, build, stops


class Targets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = {}
        self.links = {}
        self.current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'span' and attrs.get('id', '').startswith('tick-'):
            self.current = ('target', attrs['id'])
            self.targets[attrs['id']] = ''
        elif tag == 'a' and attrs.get('href', '').startswith('#tick-'):
            self.current = ('link', attrs['href'][1:])
            self.links[attrs['href'][1:]] = ''

    def handle_data(self, data):
        if self.current:
            kind, key = self.current
            (self.targets if kind == 'target' else self.links)[key] += data

    def handle_endtag(self, tag):
        if self.current and tag == ('span' if self.current[0] == 'target' else 'a'):
            self.current = None


class InputTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        root = Path(cls.temporary.name)
        shutil.copytree(ROOT / 'src', root / 'src')
        cls.directory = build(root)

    def check_group(self, prefix, labels):
        for page in ('index.html', 'samples-96.html', 'preset-weave.html'):
            parser = Targets()
            parser.feed((self.directory / page).read_text())
            actual = {key: value for key, value in parser.links.items() if key.startswith(prefix)}
            self.assertEqual(list(actual.values()), labels)
            for key, value in actual.items():
                self.assertEqual(parser.targets[key], value)

    def test_k_links_have_existing_targets_with_matching_integer_values(self):
        self.check_group('tick-k-', [f'{value:.2f}' for value in range(1, 9)])

    def test_phase_links_have_existing_targets_with_matching_degree_values(self):
        self.check_group('tick-phase-', [f'{value}°' for value in range(0, 361, 90)])

    def test_target_prefix_is_optional_and_cannot_inject_attributes(self):
        self.assertNotIn('id=', stops([1, 2], 1, str))
        self.assertIn('id="tick-k-0" tabindex="-1"', stops([1, 2], 1, str, 'tick-k'))
        for prefix in ('../x', 'bad" id="other', '', 'A'):
            with self.subTest(prefix=prefix), self.assertRaises(ValueError):
                stops([1, 2], 1, str, prefix)
