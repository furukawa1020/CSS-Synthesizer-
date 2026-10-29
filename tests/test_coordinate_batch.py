"""Replay explicit browser evidence lists without changing their files."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.coordinate_batch import inspect_batch
from tools.coordinates import main

ROOT = Path(__file__).resolve().parents[1]


class CoordinateBatchTests(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        # This is measured browser geometry, not the CSS --x/--y variables.
        snapshot = json.loads((ROOT / 'qa/evidence/batch40/model-fermat.json').read_text())
        for name in ('one.json', 'two.json'):
            (root / name).write_text(json.dumps(snapshot))
        manifest = root / 'index.json'
        manifest.write_text(json.dumps({'snapshots': ['one.json', 'two.json']}))
        return root, manifest, snapshot

    def test_success_aggregates_all_files_and_cli_keeps_single_mode(self):
        root, manifest, snapshot = self.fixture()
        before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in root.iterdir()}
        result = inspect_batch(manifest)
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['checked_files'], 2)
        self.assertEqual(result['checked_points'], 2 * len(snapshot['points']))
        self.assertEqual([r['path'] for r in result['files']], ['one.json', 'two.json'])
        self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in root.iterdir()})
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(['--batch', str(manifest)]), 0)
            self.assertEqual(main([str(root / 'one.json')]), 0)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            main([str(root / 'one.json'), '--batch', str(manifest)])
        self.assertEqual(raised.exception.code, 2)

    def test_bad_snapshot_does_not_stop_the_other_observations(self):
        root, manifest, snapshot = self.fixture()
        snapshot['points'][0]['x'] += 10
        (root / 'one.json').write_text(json.dumps(snapshot))
        result = inspect_batch(manifest)
        self.assertFalse(result['ok'])
        self.assertFalse(result['files'][0]['ok'])
        self.assertTrue(result['files'][1]['ok'])
        self.assertEqual(result['checked_files'], 2)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(['--batch', str(manifest)]), 1)

    def test_manifest_requires_unique_bounded_flat_json_names(self):
        root, manifest, _ = self.fixture()
        bad = [[], {}, {'snapshots': []}, {'snapshots': ['one.json'] * 2},
               {'snapshots': ['../one.json']}, {'snapshots': ['/one.json']},
               {'snapshots': ['sub/one.json']}, {'snapshots': ['sub\\one.json']},
               {'snapshots': ['index.json']}, {'snapshots': [True]},
               {'snapshots': ['one.json'], 'extra': True}]
        for reference in bad:
            with self.subTest(reference=reference):
                manifest.write_text(json.dumps(reference))
                self.assertFalse(inspect_batch(manifest)['ok'])
        manifest.write_text('{"snapshots":[],"snapshots":["one.json"]}')
        self.assertFalse(inspect_batch(manifest)['ok'])
        manifest.write_text('{"snapshots":[NaN]}')
        self.assertFalse(inspect_batch(manifest)['ok'])

    def test_malformed_snapshot_still_consumes_the_read_budget(self):
        root, manifest, _ = self.fixture()
        original = Path.read_bytes
        for payload in (b'x' * 15, b'\xff' * 15):
            with self.subTest(payload=payload):
                (root / 'one.json').write_bytes(payload)
                (root / 'two.json').write_bytes(payload)
                reads = []
                def read_bytes(path):
                    reads.append(path.name)
                    return original(path)
                with patch('tools.coordinate_batch.MAX_BATCH_BYTES', 20), patch.object(Path, 'read_bytes', read_bytes):
                    result = inspect_batch(manifest)
                self.assertFalse(result['ok'])
                self.assertEqual(result['checked_files'], 2)
                self.assertIn('one.json', reads)
                self.assertNotIn('two.json', reads)

    def test_missing_and_symlink_files_and_limits_are_rejected(self):
        root, manifest, _ = self.fixture()
        for kind in ('missing', 'link', 'directory'):
            path = root / 'one.json'
            if path.is_symlink() or path.is_file(): path.unlink()
            elif path.is_dir(): path.rmdir()
            if kind == 'link': path.symlink_to(root / 'two.json')
            elif kind == 'directory': path.mkdir()
            with self.subTest(kind=kind):
                self.assertFalse(inspect_batch(manifest)['ok'])
        (root / 'one.json').rmdir()
        (root / 'one.json').write_bytes((root / 'two.json').read_bytes())
        for name in ('MAX_MANIFEST_BYTES', 'MAX_SNAPSHOT_BYTES', 'MAX_BATCH_BYTES', 'MAX_SNAPSHOTS'):
            with self.subTest(limit=name), patch(f'tools.coordinate_batch.{name}', 1):
                self.assertFalse(inspect_batch(manifest)['ok'])
        link = root / 'alias.json'
        link.symlink_to(manifest)
        self.assertFalse(inspect_batch(link)['ok'])
        self.assertFalse(inspect_batch(root / 'missing.json')['ok'])
        for tolerance in (float('nan'), float('inf'), -1, True, 10 ** 1000):
            with self.subTest(tolerance=tolerance):
                self.assertFalse(inspect_batch(manifest, tolerance)['ok'])
