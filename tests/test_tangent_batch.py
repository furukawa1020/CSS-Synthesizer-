import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from tools.tangents import main, inspect_tangent_snapshot
from tools.coordinate_batch import inspect_manifest

class TangentBatchTests(unittest.TestCase):
    def test_batch_uses_degree_errors_and_continues_after_failure(self):
        source=Path(__file__).resolve().parents[1]/'qa/evidence/batch60/tangent-wave.json'
        data=json.loads(source.read_text())
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); (root/'ok.json').write_text(json.dumps(data))
            data['tangents'][0]['angle_degrees']+=90
            (root/'bad.json').write_text(json.dumps(data))
            manifest=root/'index.json';manifest.write_text(json.dumps({'snapshots':['bad.json','ok.json']}))
            result=inspect_manifest(manifest,inspect_tangent_snapshot,error_key='max_error_degrees')
            self.assertFalse(result['ok']);self.assertEqual(result['checked_files'],2)
            self.assertTrue(result['files'][1]['ok']);self.assertGreater(result['max_error_degrees'],80)
            self.assertNotIn('max_error',result)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(['--batch',str(manifest)]),1)
                self.assertEqual(main([str(root/'ok.json')]),0)
            manifest.write_text('{"snapshots":["ok.json"]}')
            with contextlib.redirect_stdout(io.StringIO()): self.assertEqual(main(['--batch',str(manifest)]),0)
            (root/'ok.json').write_text('{"model":"wave","model":"rose"}')
            with contextlib.redirect_stdout(io.StringIO()): self.assertEqual(main([str(root/'ok.json')]),1)
            (root/'ok.json').unlink();(root/'ok.json').symlink_to(root/'bad.json')
            with contextlib.redirect_stdout(io.StringIO()): self.assertEqual(main(['--batch',str(manifest)]),1)
