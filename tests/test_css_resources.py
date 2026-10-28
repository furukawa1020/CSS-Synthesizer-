"""Regression cases for decoded CSS resources, distinct from prose strings."""
import unittest

from tools.audit import audit_css, audit_html
from tools.css_resources import css_resources


class CSSResourceTests(unittest.TestCase):
    def test_escaped_function_at_rule_and_url_value_are_inspected(self):
        cases = (
            r'.plot{background:u\72l(https://example.invalid/a.png)}',
            r'.plot{background:\75\72\6c("\68 ttps\3a //example.invalid/a.png")}',
            r'@\69mport "https://example.invalid/a.css";',
            r'@im\70ort/**/url(\2f\2f example.invalid/a.css);',
            r'@IMPORT "\68ttps://example.invalid/a.css" screen;',
            r'.plot{background:URL(\6a avascript\3a alert\(1\))}',
            r'.plot{background:url("data\3a image/svg+xml,<svg/>")}',
        )
        for css in cases:
            with self.subTest(css=css):
                self.assertFalse(audit_css(css)['ok'])
                self.assertFalse(audit_html('<style>' + css + '</style>')['ok'])

    def test_comments_and_prose_do_not_create_resource_tokens(self):
        cases = (
            '/* url(https://example.invalid/x) */ .plot{color:red}',
            r'.plot::after{content:"url(https://example.invalid/x)"}',
            r'.plot::after{content:"@import \"https://example.invalid/x\""}',
            r'.plot::after{content:"/*"} /* real comment */ .plot{background:url(local.png)}',
            r'.plot{background:url("local/*literal*/name.png")}',
            r'.plot{background:url(local\)name.png);width:calc(sin(1rad)*1px)}',
            r'.plot{background:url("data:image/png;base64,AA==")}',
            r'.plot{background:url(\6c ocal.png)}',
        )
        for css in cases:
            with self.subTest(css=css):
                self.assertTrue(audit_css(css)['ok'], audit_css(css)['errors'])

    def test_escaped_quotes_are_values_not_string_delimiters(self):
        css = r'.plot{background:url("https://example.invalid/a\"b.png")} .plot::after{content:"ignored"}'
        self.assertEqual(list(css_resources(css)), ['https://example.invalid/a"b.png'])
        self.assertFalse(audit_css(css)['ok'])

    def test_string_continuation_and_hex_terminator_whitespace_are_decoded(self):
        css = '.plot{background:url("https:\\\n//example.invalid/x")}'
        self.assertEqual(list(css_resources(css)), ['https://example.invalid/x'])
        self.assertFalse(audit_css(css)['ok'])
        self.assertEqual(list(css_resources(r'@\000069 mport "local.css";')), ['local.css'])

    def test_unquoted_escaped_parenthesis_does_not_end_url(self):
        self.assertEqual(list(css_resources(r'.plot{background:url(local\)file.png)}')), ['local)file.png'])


if __name__ == '__main__':
    unittest.main()
