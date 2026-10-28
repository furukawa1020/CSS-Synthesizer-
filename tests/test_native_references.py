from pathlib import Path
import tempfile
import unittest

from tools.audit import audit_html, audit_directory, audit_document_links
from tools.assets import asset_specs

_PAGES = tuple((name, count) for name, count in asset_specs() if count is not None)


class NativeReferenceTests(unittest.TestCase):
    def test_unexpanded_or_malformed_fragment_markers_cannot_pass(self):
        for marker in ('@@FRAGMENT:dialog@@', '@@FRAGMENT:@@'):
            with self.subTest(marker=marker):
                self.assertFalse(audit_html(marker)['ok'])

    def test_forward_references_native_controls_and_aria_are_allowed(self):
        source = '''<button type="button" command="show-modal" commandfor="help">開く</button>
        <button type="button" popovertarget="settings">設定</button><label for="choice">選択</label>
        <output for="choice" aria-labelledby="caption" aria-describedby="description"></output>
        <input id="choice"><p id="caption">名前</p><p id="description">説明</p>
        <div popover id="settings"></div><dialog id="help">
        <button type="button" command="request-close" commandfor="help">閉じる</button></dialog>'''
        result = audit_html(source)
        self.assertTrue(result['ok'], result['errors'])

    def test_duplicate_missing_and_wrong_type_references_fail(self):
        cases = [
            '<div id="a"></div><p id="a"></p>',
            '<button popovertarget="missing"></button>',
            '<button popovertarget="a"></button><div id="a"></div>',
            '<button commandfor="a" command="show-modal"></button><div id="a"></div>',
            '<button commandfor="a" command="toggle-popover"></button><dialog id="a"></dialog>',
            '<label for="a">名前</label><p id="a"></p>',
            '<input aria-describedby="missing">',
            '<output for="missing"></output>',
            '<button command="close"></button>',
            '<button commandfor="a" command="--custom"></button><div id="a"></div>',
        ]
        for source in cases:
            with self.subTest(source=source):
                self.assertFalse(audit_html(source)['ok'])

    def test_popover_command_can_target_a_non_dialog_popover(self):
        result = audit_html('<button type="button" commandfor="p" command="show-popover"></button><aside id="p" popover></aside>')
        self.assertTrue(result['ok'], result['errors'])

    def test_native_command_buttons_explicitly_avoid_form_submission_and_reset(self):
        for control, target in (
            ('commandfor="p" command="show-modal"', '<dialog id="p"></dialog>'),
            ('popovertarget="p"', '<div id="p" popover></div>'),
        ):
            for kind in (None, 'submit', 'reset'):
                with self.subTest(control=control, kind=kind):
                    attribute = '' if kind is None else f'type="{kind}"'
                    result = audit_html(f'<form><button {attribute} {control}>開く</button>{target}</form>')
                    self.assertFalse(result['ok'])
                    self.assertIn('type="button"', '\n'.join(result['errors']))
            result = audit_html(f'<form><button type="BUTTON" {control}>開く</button>{target}</form>')
            self.assertTrue(result['ok'], result['errors'])

    def test_popover_actions_are_case_insensitive_and_input_must_be_a_button(self):
        self.assertTrue(audit_html('<input type="button" popovertarget="p" popovertargetaction="SHOW"><div id="p" popover></div>')['ok'])
        for kind in ('text', 'radio', 'hidden', ''):
            with self.subTest(kind=kind):
                self.assertFalse(audit_html(f'<input type="{kind}" popovertarget="p"><div id="p" popover></div>')['ok'])

    def test_fragment_navigation_decodes_ids_and_preserves_top_or_text_navigation(self):
        for href in ('#', '#top', '#TOP', '#:~:text=sample', '#%E5%BC%8F'):
            with self.subTest(href=href):
                self.assertTrue(audit_html(f'<a href="{href}">移動</a><p id="式"></p>')['ok'])
        self.assertFalse(audit_html('<a href="#missing">移動</a>')['ok'])
        self.assertTrue(audit_html('<a href="https://example.invalid/#missing">資料</a>')['ok'])

    def test_cross_document_file_and_fragment_targets_are_checked(self):
        documents = {'index.html': '<a href="other.html#target">移動</a><link rel="stylesheet" href="style.css">',
                     'other.html': '<p id="target"></p>'}
        self.assertFalse(any(audit_document_links(documents, {*documents, 'style.css'}).values()))
        for href in ('missing.html', 'other.html#missing', '../other.html', 'other.html#%6dissing'):
            with self.subTest(href=href):
                invalid = {**documents, 'index.html': f'<a href="{href}">移動</a>'}
                self.assertTrue(audit_document_links(invalid, {*documents, 'style.css'})['index.html'])

    def test_directory_audit_adds_cross_page_failures_to_the_origin_page(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name, count in _PAGES:
                (root / name).write_text('<i class="sample"></i>' * count)
            (root / 'style.css').write_text('')
            (root / 'engine.css').write_text('')
            with (root / 'index.html').open('a') as stream:
                stream.write('<a href="samples-96.html#missing">移動</a>')
            result = audit_directory(root)
            self.assertFalse(result['ok'])
            self.assertIn('index.html:', result['errors'][0])
