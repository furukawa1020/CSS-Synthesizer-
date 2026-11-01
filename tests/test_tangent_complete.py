import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from tools.tangents import inspect_tangent_snapshot, main

class CompleteTangentTests(unittest.TestCase):
    def test_missing_sample_is_only_allowed_in_default_partial_mode(self):
        data=json.loads((Path(__file__).resolve().parents[1]/'qa/evidence/batch80/tangent-02-wave.json').read_text())
        self.assertTrue(inspect_tangent_snapshot(data,require_all=True)['ok'])
        data['tangents'].pop()
        self.assertTrue(inspect_tangent_snapshot(data)['ok'])
        self.assertFalse(inspect_tangent_snapshot(data,require_all=True)['ok'])
        self.assertFalse(inspect_tangent_snapshot(data,require_all='yes')['ok'])
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path=root/'one.json';path.write_text(json.dumps(data));manifest=root/'index.json';manifest.write_text(json.dumps({'snapshots':['one.json']}))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main([str(path)]),0)
                self.assertEqual(main([str(path),'--require-all']),1)
                self.assertEqual(main(['--batch',str(manifest),'--require-all']),1)
