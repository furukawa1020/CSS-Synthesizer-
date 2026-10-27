"""HTML/CSS専用成果物の静的ガードと、実際のすり抜けの回帰テスト。"""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.audit import _PAGES, audit_css, audit_directory, audit_html


def points(count: int) -> str:
    return '<div class="plot">' + '<i class="sample"></i>' * count + '</div>'


class AuditTests(unittest.TestCase):
    def test_local_resources_native_controls_and_explanatory_links_are_allowed(self):
        html = '''<!doctype html><html lang="ja"><head>
          <meta http-equiv="Content-Security-Policy" content="script-src 'none'">
          <link rel="stylesheet" href="style.css"><link rel="icon" href="data:,">
          </head><body><input type="radio" name="model"><details><summary>式</summary>
          <code>&lt;script&gt; は使わない</code><a href="https://developer.mozilla.org/">資料</a>
          </details><!-- <script src="https://example.invalid/unused.js"></script> -->
          <p title="k > 1">値</p>''' + points(2) + '</body></html>'
        self.assertEqual(audit_html(html, 2), {"ok": True, "errors": [], "sample_count": 2})

    def test_script_and_alternate_render_elements_are_forbidden(self):
        for html in (
            '<ScRiPt type="module"></ScRiPt>',
            '<script type="application/json">{}</script>',
            '<canvas></canvas>', '<svg viewBox="0 0 1 1"></svg>',
        ):
            with self.subTest(html=html):
                self.assertFalse(audit_html(html)["ok"])

    def test_active_embeds_are_rejected_for_data_local_and_missing_urls(self):
        # data: URLs previously passed the original guard. Reject the embed
        # itself so URL location or encoding cannot change the policy.
        for html in (
            '<iframe src="data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg=="></iframe>',
            '<object data="data:text/html,test"></object>',
            '<EMBED src="data:application/pdf,test">',
            '<iframe src="./help.html"></iframe>',
            '<iframe></iframe>', '<object><p>代替テキスト</p></object>',
            '<iframe srcdoc="&lt;p&gt;別文書&lt;/p&gt;"></iframe>',
        ):
            with self.subTest(html=html):
                self.assertIn("禁止された要素", "\n".join(audit_html(html)["errors"]))

    def test_event_attributes_are_detected_with_varied_quoting_and_case(self):
        for html in (
            '<button onclick="x()">', '<input ONFOCUS=x()>',
            "<img onerror = 'x()' src=\"local.png\">",
        ):
            with self.subTest(html=html):
                self.assertIn("イベントハンドラ属性", "\n".join(audit_html(html)["errors"]))
        self.assertTrue(audit_html('<p data-on="value" class="only">説明</p>')["ok"])

    def test_character_references_and_ascii_whitespace_cannot_hide_script_urls(self):
        for value in (
            'javascript:alert(1)', 'JaVaScRiPt:alert(1)',
            '&#106;avascript&#58;alert(1)', 'java&#x09;script&colon;alert(1)',
            '&#x6a;avascript:alert(1)',
        ):
            with self.subTest(value=value):
                self.assertIn("javascript:", "\n".join(audit_html(f'<a href="{value}">移動</a>')["errors"]))

    def test_runtime_external_resources_are_distinguished_from_navigation_links(self):
        for html in (
            '<link rel="stylesheet" href="https://example.invalid/main.css">',
            '<img src="//example.invalid/a.png">',
            '<source srcset="local.png 1x, https://example.invalid/a.png 2x">',
            '<iframe src="https://example.invalid/"></iframe>',
            '<base href="https://example.invalid/"><link rel="stylesheet" href="relative.css">',
            '<form action="https://example.invalid/submit"></form>',
            '<style>@import "https://example.invalid/font.css";</style>',
            '<p style="background:url(https://example.invalid/a.png)">',
            '<a href="./" ping="https://example.invalid/track">移動</a>',
            '<img src="data:image/svg+xml,&lt;svg/&gt;">',
        ):
            with self.subTest(html=html):
                self.assertFalse(audit_html(html)["ok"])
        self.assertTrue(audit_html(
            '<link rel="canonical" href="https://example.invalid/">'
            '<p style="background:url(local.png)">'
        )["ok"])

    def test_inline_css_character_references_are_decoded_by_the_html_parser(self):
        result = audit_html('<p style="background:url(https&colon;//example.invalid/a.png)">')
        self.assertIn("外部CSSリソース", "\n".join(result["errors"]))

    def test_only_actual_i_sample_elements_are_counted(self):
        html = points(3) + '<i class="sample-extra"></i><span class="sample"></span><!-- <i class="sample"></i> -->'
        self.assertTrue(audit_html(html, 3)["ok"])
        self.assertEqual(audit_html(html)["sample_count"], 3)
        self.assertIn("expected 4, got 3", "\n".join(audit_html(html, 4)["errors"]))
        self.assertEqual(audit_html('<i class="samp&#108;e"/>')["sample_count"], 1)

    def test_template_tokens_are_rejected_and_css_calculations_are_allowed(self):
        for token in ('{{SAMPLES}}', '__SAMPLE_POINTS__', '@@SAMPLES@@', '<!--POINTS-->'):
            with self.subTest(token=token):
                self.assertIn("テンプレートトークン", "\n".join(audit_html(token)["errors"]))
        self.assertTrue(audit_html('<style>.sample{left:calc(50% + var(--x) * 1px)}</style>')["ok"])

    def test_external_css_urls_and_imports_are_rejected(self):
        for css in (
            '@import "https://example.invalid/font.css";',
            '@import url(//example.invalid/theme.css);',
            '@font-face{font-family:Test;src:url("https://example.invalid/font.woff2")}',
            '.plot{background-image:url(https://example.invalid/a.png)}',
        ):
            with self.subTest(css=css):
                self.assertIn("外部CSSリソース", "\n".join(audit_css(css)["errors"]))
        self.assertEqual(audit_css(
            '/* @import "https://example.invalid/unused.css"; */ .plot{background:url(local.png)}'
        ), {"ok": True, "errors": []})

    def test_meta_refresh_is_not_a_local_navigation_escape(self):
        result = audit_html('<meta http-equiv="refresh" content="0;url=https://example.invalid/">')
        self.assertFalse(result["ok"])
        self.assertIn("meta refresh", "\n".join(result["errors"]))

    def test_wrong_types_and_nonpositive_sample_counts_are_errors(self):
        for value in (None, 1, b"text"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    audit_html(value)
                with self.assertRaises(TypeError):
                    audit_css(value)
        for samples in (0, -1, 1.5, True):
            with self.subTest(samples=samples):
                with self.assertRaises(TypeError):
                    audit_html("", samples)

    def test_directory_and_cli_report_good_broken_and_missing_assets(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix="css-synth-audit-") as temporary:
            directory = Path(temporary)
            for filename, count in _PAGES:
                (directory / filename).write_text(points(count), encoding="utf-8")
            (directory / "style.css").write_text('body{color:#222}', encoding="utf-8")
            (directory / "engine.css").write_text('.sample{left:50%;top:50%}', encoding="utf-8")
            result = audit_directory(directory)
            self.assertTrue(result["ok"])
            self.assertEqual(len(result["files"]), len(_PAGES) + 2)
            good = subprocess.run(
                [sys.executable, "-m", "tools.audit", str(directory)],
                cwd=root, capture_output=True, text=True,
            )
            self.assertEqual(good.returncode, 0, good.stderr)
            self.assertEqual(good.stdout.count("PASS "), len(_PAGES) + 2)
            (directory / "index.html").write_text(points(192) + '<script></script>', encoding="utf-8")
            (directory / "style.css").write_text('@import "https://example.invalid/theme.css";', encoding="utf-8")
            (directory / "samples-96.html").unlink()
            bad_result = audit_directory(directory)
            self.assertFalse(bad_result["ok"])
            self.assertEqual(sum(not item["ok"] for item in bad_result["files"]), 3)
            bad = subprocess.run(
                [sys.executable, "-m", "tools.audit", str(directory)],
                cwd=root, capture_output=True, text=True,
            )
            self.assertEqual(bad.returncode, 1)
            for filename in ("index.html", "samples-96.html", "style.css"):
                self.assertIn(f"FAIL {filename}", bad.stderr)
            self.assertIn("PASS samples-384.html", bad.stdout)
            self.assertIn("PASS engine.css", bad.stdout)


if __name__ == "__main__":
    unittest.main()
