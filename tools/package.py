"""Audit and package the static synthesizer using Python's standard library."""

import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

from .audit import audit_css, audit_html
from .build import build
from .assets import asset_specs


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_NAME = "css-synthesizer-v0.1.zip"
MANIFEST_NAME = "css-synthesizer-v0.1.manifest.json"
INSTRUCTIONS = """CSS視覚シンセサイザー v0.1

index.htmlと2つのCSSを同じ場所に置き、現行Chrome / Edgeで開いてください。
点数比較用のsamples-96.html、samples-384.htmlと、停止状態で始めるpreset-*.htmlも同梱しています。
gallery.htmlで停止した形を一覧比較できます。
ブラウザ内の実行コードはHTML / CSSのみです。音声・永続保存はありません。
非対応環境では画面に示す制限を確認してください。
実機タッチ・他ブラウザ・実OSの動きを減らす設定・性能の確認状況は、
リポジトリの受け入れ記録とIssue #3を参照してください。

SHA256SUMSは同梱したアプリファイルのSHA-256です。
ZIP全体のSHA-256と生成元commitは、ZIPの隣のmanifest.jsonに記録します。
ソース: https://github.com/furukawa1020/CSS-Synthesizer-
"""


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def package_release(build_directory, output_directory, source_revision, *, assets=None):
    """Package only this project's audited assets; do not regenerate API input."""
    build_directory = Path(build_directory)
    output_directory = Path(output_directory)
    specs = asset_specs() if assets is None else tuple(assets)
    names = {path.name for path in build_directory.iterdir()}
    allowed = {name for name, _ in specs}
    unexpected = sorted(names - allowed)
    missing = [name for name, _ in specs if name not in names]
    if unexpected:
        raise ValueError(f"許可されていない配布ファイル: {', '.join(unexpected)}")
    if missing:
        raise ValueError(f"配布ファイルが不足しています: {', '.join(missing)}")
    if not isinstance(source_revision, str) or not re.fullmatch(r"[a-f0-9]{40}", source_revision):
        raise ValueError("生成元の完全なcommit SHAが必要です")

    entries = []
    checksums = []
    for name, samples in specs:
        path = build_directory / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"通常ファイルではありません: {name}")
        data = path.read_bytes()
        text = data.decode("utf-8")
        result = audit_css(text) if samples is None else audit_html(text, samples=samples)
        if not result["ok"]:
            raise ValueError(f"{name}の静的監査に失敗しました: {'; '.join(result['errors'])}")
        entries.append((name, data))
        checksums.append(f"{sha256(data)}  {name}")
    entries.extend((
        ("README.txt", INSTRUCTIONS.encode("utf-8")),
        ("SHA256SUMS", ("\n".join(checksums) + "\n").encode("utf-8")),
    ))

    # These small files use STORE, so compressor versions cannot change
    # their bytes. Explicit date, order, platform and permissions omit host data.
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED, allowZip64=False) as archive:
        for name, data in entries:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.create_version = 20
            info.extract_version = 20
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    archive_bytes = buffer.getvalue()
    manifest = {
        "version": "0.1",
        "archive": ARCHIVE_NAME,
        "sha256": sha256(archive_bytes),
        "sourceRevision": source_revision,
        "files": [
            {"name": name, "bytes": len(data), "sha256": sha256(data)}
            for name, data in entries
        ],
    }
    output_directory.mkdir(parents=True, exist_ok=True)
    (output_directory / ARCHIVE_NAME).write_bytes(archive_bytes)
    (output_directory / MANIFEST_NAME).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main():
    try:
        changes = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=normal"],
            cwd=ROOT, check=True, capture_output=True, text=True,
        ).stdout
        if changes.strip():
            raise ValueError("未コミットの変更があります。変更をcommitしてから生成してください")
        source_revision = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT,
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        build_directory = build(root=ROOT)
        manifest = package_release(build_directory, ROOT / "dist", source_revision)
        print(f"配布ZIPを生成しました: dist/{manifest['archive']}")
        print(f"SHA-256: {manifest['sha256']}\n生成元: {manifest['sourceRevision']}")
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        print(f"配布ZIPを生成できませんでした: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
