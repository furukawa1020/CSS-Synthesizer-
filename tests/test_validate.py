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
