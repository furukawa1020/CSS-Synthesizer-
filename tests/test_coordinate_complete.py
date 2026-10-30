import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from tools.coordinates import inspect_snapshot, main
from tools.coordinate_batch import inspect_batch

class CompleteCoordinatesTests(unittest.TestCase):
    def test_partial_observation_is_opt_in_and_strict_mode_reaches_cli_and_batch(self):
        source=Path(__file__).resolve().parents[1]/'qa/evidence/batch60/coord-compare-wave.json'
        snapshot=json.loads(source.read_text())
        self.assertTrue(inspect_snapshot(snapshot, require_all=True)['ok'])
        snapshot['points'].pop()
        self.assertTrue(inspect_snapshot(snapshot)['ok'])
        self.assertFalse(inspect_snapshot(snapshot, require_all=True)['ok'])
        self.assertFalse(inspect_snapshot(snapshot, require_all='yes')['ok'])
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); path=root/'one.json'; path.write_text(json.dumps(snapshot))
            manifest=root/'index.json'; manifest.write_text(json.dumps({'snapshots':['one.json']}))
            self.assertTrue(inspect_batch(manifest)['ok'])
            self.assertFalse(inspect_batch(manifest, require_all=True)['ok'])
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main([str(path),'--require-all']),1)
                self.assertEqual(main(['--batch',str(manifest),'--require-all']),1)
