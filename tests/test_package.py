"""Distribution checks; browser behavior is checked separately."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from tools.package import package_release
from tools.assets import asset_specs

ASSETS = asset_specs()


ROOT = Path(__file__).resolve().parents[1]
REVISION_A = "1" * 40
REVISION_B = "2" * 40
APP_NAMES = [name for name, _ in ASSETS]
EXPECTED_NAMES = [*APP_NAMES, 'README.txt', 'SHA256SUMS']


def digest(data):
    return hashlib.sha256(data).hexdigest()


class PackageTests(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory(prefix="css-synth-package-")
        self.addCleanup(temporary.cleanup)
        directory = Path(temporary.name)
        build_directory = directory / "build"
        build_directory.mkdir()
        for name, count in ASSETS:
            if count is None:
                continue
            page = '<!doctype html><html lang="ja"><title>fixture</title>'
            page += '<i class="sample"></i>' * count
            (build_directory / name).write_text(page + "</html>", encoding="utf-8")
        (build_directory / "style.css").write_text("abc", encoding="utf-8")
        (build_directory / "engine.css").write_text(".sample { color: black; }", encoding="utf-8")
        return build_directory, directory / "dist"

    def test_archive_content_and_checksums(self):
        build_directory, output_directory = self.fixture()
        manifest = package_release(build_directory, output_directory, REVISION_A)
        archive_path = output_directory / manifest["archive"]
        archive_bytes = archive_path.read_bytes()
        with zipfile.ZipFile(archive_path) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(archive.namelist(), EXPECTED_NAMES)
            for name in APP_NAMES:
                self.assertEqual(archive.read(name), (build_directory / name).read_bytes())
            for info in archive.infolist():
                self.assertEqual(info.compress_type, zipfile.ZIP_STORED)
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
                self.assertEqual(info.create_system, 3)
                self.assertEqual(info.external_attr >> 16, 0o100644)
            self.assertEqual(archive.getinfo("style.css").CRC, 0x352441C2)
            checksums = "".join(f"{digest(archive.read(name))}  {name}\n" for name in APP_NAMES)
            self.assertEqual(archive.read("SHA256SUMS").decode("utf-8"), checksums)
            expected_files = [
                {"name": name, "bytes": len(archive.read(name)), "sha256": digest(archive.read(name))}
                for name in EXPECTED_NAMES
            ]
            self.assertEqual(manifest["files"], expected_files)
        self.assertEqual(manifest["sha256"], digest(archive_bytes))
        self.assertEqual(manifest["sourceRevision"], REVISION_A)
        saved = json.loads((output_directory / "css-synthesizer-v0.1.manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(saved, manifest)
        self.assertNotIn(REVISION_A.encode(), archive_bytes)

    def test_same_inputs_reproduce_despite_mtime_and_commit_changes(self):
        build_directory, output_directory = self.fixture()
        first = package_release(build_directory, output_directory, REVISION_A)
        first_bytes = (output_directory / first["archive"]).read_bytes()
        for path in build_directory.iterdir():
            os.utime(path, (1234567890, 1234567890))
        second = package_release(build_directory, output_directory, REVISION_B)
        self.assertEqual((output_directory / second["archive"]).read_bytes(), first_bytes)
        self.assertEqual(first["sha256"], second["sha256"])
        self.assertNotEqual(first["sourceRevision"], second["sourceRevision"])
        (build_directory / "style.css").write_text(".sample { color: white; }", encoding="utf-8")
        changed = package_release(build_directory, output_directory, REVISION_A)
        self.assertNotEqual(changed["sha256"], first["sha256"])

    def test_rejects_extra_missing_and_nonregular_files(self):
        for kind in ("qa", "directory", "missing", "symlink"):
            with self.subTest(kind=kind):
                build_directory, output_directory = self.fixture()
                if kind == "qa":
                    (build_directory / "qa-test.html").write_text("QA only", encoding="utf-8")
                elif kind == "directory":
                    (build_directory / "qa").mkdir()
                else:
                    (build_directory / "style.css").unlink()
                    if kind == "symlink":
                        (build_directory / "style.css").symlink_to(build_directory / "engine.css")
                with self.assertRaisesRegex(ValueError, "許可されていない|不足|通常ファイル"):
                    package_release(build_directory, output_directory, REVISION_A)
                self.assertFalse(output_directory.exists())

    def test_rejects_forbidden_script_and_invalid_revision(self):
        build_directory, output_directory = self.fixture()
        with self.assertRaisesRegex(ValueError, "commit SHA"):
            package_release(build_directory, output_directory, "HEAD")
        page = build_directory / "index.html"
        page.write_text(page.read_text(encoding="utf-8") + "<script>alert(1)</script>", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "静的監査"):
            package_release(build_directory, output_directory, REVISION_A)

    def test_cli_rejects_dirty_tree_or_rebuilds_clean_head(self):
        changes = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=normal"], cwd=ROOT,
            check=True, capture_output=True, text=True,
        ).stdout
        if changes.strip():
            result = subprocess.run(
                [sys.executable, "-m", "tools.package"], cwd=ROOT,
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("未コミットの変更", result.stderr)
            return
        build_directory = ROOT / "build"
        build_directory.mkdir(exist_ok=True)
        (build_directory / "index.html").write_text("<script>old-build-must-not-be-packaged</script>", encoding="utf-8")
        (build_directory / "qa-stale.html").write_text("old QA fixture", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-m", "tools.package"], cwd=ROOT,
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((build_directory / "qa-stale.html").exists())
        manifest = json.loads((ROOT / "dist/css-synthesizer-v0.1.manifest.json").read_text(encoding="utf-8"))
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT,
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        self.assertEqual(manifest["sourceRevision"], revision)
        archive_path = ROOT / "dist" / manifest["archive"]
        self.assertEqual(manifest["sha256"], digest(archive_path.read_bytes()))
        with zipfile.ZipFile(archive_path) as archive:
            page = archive.read("index.html")
        self.assertEqual(page, (build_directory / "index.html").read_bytes())
        self.assertNotIn(b"old-build-must-not-be-packaged", page)


if __name__ == "__main__":
    unittest.main()
