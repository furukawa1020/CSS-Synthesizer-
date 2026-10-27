import hashlib
import io
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from tools.package import ASSETS, package_release
from tools.verify import verify_archive


class ArchiveVerificationTests(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        source = root / 'build'
        source.mkdir()
        for name, count in ASSETS:
            text = ('<i class="sample"></i>' * count) if count is not None else 'body{color:black}'
            (source / name).write_text(text, encoding='utf-8')
        manifest = package_release(source, root / 'dist', '1' * 40)
        return root / 'dist' / manifest['archive'], root / 'dist' / 'css-synthesizer-v0.1.manifest.json'

    def rewrite(self, path, change):
        with zipfile.ZipFile(path) as archive:
            entries = [(info, archive.read(info)) for info in archive.infolist()]
        result = io.BytesIO()
        with zipfile.ZipFile(result, 'w') as archive:
            for info, data in change(entries):
                archive.writestr(info, data)
        path.write_bytes(result.getvalue())

    def test_generated_zip_and_external_manifest_pass_without_extracting(self):
        archive, manifest = self.fixture()
        before = set(archive.parent.iterdir())
        result = verify_archive(archive, manifest)
        self.assertTrue(result['ok'], result['errors'])
        self.assertTrue(result['manifest_verified'])
        self.assertEqual(result['sha256'], hashlib.sha256(archive.read_bytes()).hexdigest())
        self.assertEqual(set(archive.parent.iterdir()), before)
        self.assertFalse(verify_archive(archive)['manifest_verified'])

    def test_tamper_and_external_manifest_mismatch_are_rejected(self):
        archive, manifest = self.fixture()
        self.rewrite(archive, lambda entries: [(info, b'body{color:red}' if info.filename == 'style.css' else data) for info, data in entries])
        self.assertFalse(verify_archive(archive)['ok'])
        self.assertFalse(verify_archive(archive, manifest)['ok'])

    def test_duplicate_missing_dangerous_name_and_nonregular_member_are_rejected(self):
        for kind in ('duplicate', 'missing', 'traversal', 'backslash', 'symlink', 'directory', 'dos-directory'):
            with self.subTest(kind=kind):
                archive, _ = self.fixture()
                def change(entries):
                    if kind == 'duplicate':
                        return [*entries, entries[0]]
                    if kind == 'missing':
                        return entries[1:]
                    info, data = entries[0]
                    if kind == 'traversal':
                        info.filename = '../index.html'
                    elif kind == 'backslash':
                        info.filename = '..\\index.html'
                    elif kind == 'symlink':
                        info.external_attr = (stat.S_IFLNK | 0o777) << 16
                    elif kind == 'directory':
                        info.external_attr = (stat.S_IFDIR | 0o755) << 16
                    else:
                        info.external_attr = 0x10
                    return [(info, data), *entries[1:]]
                self.rewrite(archive, change)
                self.assertFalse(verify_archive(archive)['ok'])

    def test_compressed_members_are_outside_the_distribution_format(self):
        archive, _ = self.fixture()
        def compress(entries):
            for info, _ in entries:
                info.compress_type = zipfile.ZIP_DEFLATED
            return entries
        self.rewrite(archive, compress)
        result = verify_archive(archive)
        self.assertFalse(result['ok'])
        self.assertIn('無圧縮', result['errors'][0])

    def test_updated_internal_hash_does_not_allow_script(self):
        archive, _ = self.fixture()
        def change(entries):
            content = {info.filename: data for info, data in entries}
            content['index.html'] += b'<script></script>'
            content['SHA256SUMS'] = ''.join(f'{hashlib.sha256(content[name]).hexdigest()}  {name}\n' for name, _ in ASSETS).encode()
            return [(info, content[info.filename]) for info, _ in entries]
        self.rewrite(archive, change)
        result = verify_archive(archive)
        self.assertFalse(result['ok'])
        self.assertIn('静的監査', result['errors'][0])

    def test_updated_internal_hash_does_not_allow_a_broken_cross_page_link(self):
        archive, _ = self.fixture()
        def change(entries):
            content = {info.filename: data for info, data in entries}
            content['index.html'] += b'<a href="samples-96.html#missing">link</a>'
            content['SHA256SUMS'] = ''.join(f'{hashlib.sha256(content[name]).hexdigest()}  {name}\n' for name, _ in ASSETS).encode()
            return [(info, content[info.filename]) for info, _ in entries]
        self.rewrite(archive, change)
        result = verify_archive(archive)
        self.assertFalse(result['ok'])
        self.assertIn('参照監査', result['errors'][0])

    def test_member_archive_and_total_size_limits_are_checked(self):
        archive, _ = self.fixture()
        for constant in ('MAX_ARCHIVE_BYTES', 'MAX_MEMBER_BYTES', 'MAX_TOTAL_BYTES'):
            with self.subTest(constant=constant), patch(f'tools.verify.{constant}', 10):
                self.assertFalse(verify_archive(archive)['ok'])

    def test_invalid_checksum_list_manifest_and_zip_are_reported(self):
        for kind in ('checksum', 'manifest', 'zip'):
            with self.subTest(kind=kind):
                archive, manifest = self.fixture()
                if kind == 'checksum':
                    self.rewrite(archive, lambda entries: [(info, b'bad\n' if info.filename == 'SHA256SUMS' else data) for info, data in entries])
                elif kind == 'manifest':
                    manifest.write_text(json.dumps({'sha256': '0' * 64}))
                else:
                    archive.write_bytes(b'not a zip')
                self.assertFalse(verify_archive(archive, manifest if kind == 'manifest' else None)['ok'])

    def test_cli_returns_success_and_failure(self):
        archive, manifest = self.fixture()
        command = [sys.executable, '-m', 'tools.verify', str(archive), '--manifest', str(manifest)]
        good = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertTrue(json.loads(good.stdout)['ok'])
        archive.write_bytes(b'bad')
        bad = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(bad.returncode, 1)
        self.assertFalse(json.loads(bad.stdout)['ok'])
