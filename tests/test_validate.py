import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools.validate import validate, main

class ValidateTests(unittest.TestCase):
    def test_failed_build_does_not_skip_later_checks_or_repair(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch('tools.validate.audit_source', return_value={'ok':True,'errors':[]}), patch('tools.validate.check_build', return_value={'ok':False,'errors':['stale']}), patch('tools.validate.asset_specs', return_value=()), patch('tools.validate.audit_directory', return_value={'ok':True,'errors':[]}) as later:
                result = validate(root)
            self.assertFalse(result['ok'])
            later.assert_called_once()
            self.assertEqual(list(root.iterdir()), [])

    def test_cli_reports_failure(self):
        with patch('tools.validate.validate', return_value={'ok':False,'checks':[{'name':'broken','ok':False,'errors':['bad']}]}), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main([]), 1)

    def test_evidence_requires_manifests_and_rejects_symlink_batches(self):
        from tools.validate import evidence_checks
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertFalse(evidence_checks(root)[0]['ok'])
            (root/'batch1').symlink_to(root, target_is_directory=True)
            self.assertFalse(evidence_checks(root)[0]['ok'])

    def test_malformed_manifest_is_a_failed_check(self):
        from tools.validate import evidence_checks
        with tempfile.TemporaryDirectory() as folder:
            batch = Path(folder)/'batch1'; batch.mkdir()
            (batch/'index.json').write_text('{"snapshots":[]}')
            result = evidence_checks(Path(folder))
            self.assertEqual(result[0]['name'], 'batch1/index.json')
            self.assertFalse(result[0]['ok'])

    def test_json_output_preserves_failure_and_diagnostics(self):
        result = {'ok':False,'checks':[{'name':'test','ok':False,'errors':['診断']}]}
        out = io.StringIO()
        with patch('tools.validate.validate', return_value=result), contextlib.redirect_stdout(out):
            self.assertEqual(main(['--json']), 1)
        self.assertEqual(json.loads(out.getvalue()), result)
