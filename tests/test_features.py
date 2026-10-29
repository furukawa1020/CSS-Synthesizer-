"""Syntax checks are rendered with @supports, never guessed from the user agent."""
from html.parser import HTMLParser
import unittest
from tools.audit import audit_html
from tools.features import FEATURES, features_html


class FeaturesTests(unittest.TestCase):
    def test_diagnostic_uses_each_literal_supports_condition_and_no_samples(self):
        page = features_html()
        self.assertTrue(audit_html(page, samples=0)['ok'])
        self.assertFalse(audit_html(page + '<i class="sample"></i>', samples=0)['ok'])
        class Parser(HTMLParser):
            def __init__(self):
                super().__init__(); self.ids = []; self.script = False
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if 'id' in attrs:
                    self.ids.append(attrs['id'])
                self.script |= tag == 'script'
        parsed = Parser(); parsed.feed(page)
        self.assertFalse(parsed.script)
        self.assertEqual(parsed.ids, [f'feature-{row[0]}' for row in FEATURES])
        self.assertEqual(len(set(parsed.ids)), len(FEATURES))
        for identifier, _, _, condition, _, _ in FEATURES:
            self.assertIn('@supports ' + condition, page)
            self.assertIn(f'#feature-{identifier} .feature-no', page)
            self.assertIn(f'#feature-{identifier} .feature-yes', page)

    def test_behavior_only_capabilities_remain_explicit_manual_checks(self):
        page = features_html()
        self.assertIn('@propertyの登録とアニメーション', page)
        self.assertIn('Invoker Commands、Dialog、Popover', page)
        self.assertIn('@starting-style', page)
        self.assertIn('@counter-styleの桁埋め', page)
        self.assertIn('構文を受理することと、入力・描画・フォーカス・性能が正しく動くことは別', page)
        self.assertNotIn('feature-property', page)
        self.assertNotIn('feature-commandfor', page)
