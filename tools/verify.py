"""Verify this project's ZIP without extraction; checksums are not signatures."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import stat
import sys
import zipfile

from .audit import audit_css, audit_html, audit_document_links
from .json_data import load_json

MAX_ARCHIVE_BYTES = 16 * 1024 * 1024
MAX_MEMBER_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 8 * 1024 * 1024


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _validate_manifest(reference, archive_hash, contents):
    """Validate the current manifest format against every actual ZIP member."""
    from .package import ARCHIVE_NAME, VERSION
    required = {'version', 'archive', 'sha256', 'sourceRevision', 'files'}
    if not isinstance(reference, dict) or set(reference) != required:
        raise ValueError('manifestの項目が配布形式と一致しません')
    if reference['version'] != VERSION or reference['archive'] != ARCHIVE_NAME:
        raise ValueError('manifestのversion・archiveが配布形式と一致しません')
    revision = reference['sourceRevision']
    if not isinstance(revision, str) or not re.fullmatch(r'[a-f0-9]{40}', revision):
        raise ValueError('manifestのsourceRevisionには完全なcommit SHAが必要です')
    digest = reference['sha256']
    if not isinstance(digest, str) or not re.fullmatch(r'[a-f0-9]{64}', digest) or digest != archive_hash:
        raise ValueError('外部manifestとZIP全体のSHA-256が一致しません')
    descriptions = reference['files']
    if not isinstance(descriptions, list) or len(descriptions) != len(contents):
        raise ValueError('manifestのfilesがZIP全ファイルを記述していません')
    seen = set()
    for entry in descriptions:
        if not isinstance(entry, dict) or set(entry) != {'name', 'bytes', 'sha256'}:
            raise ValueError('manifestのファイル記述の形式が不正です')
        name = entry['name']
        if not isinstance(name, str) or name in seen or name not in contents:
            raise ValueError('manifestのファイル名が不正または重複しています')
        seen.add(name)
        size = entry['bytes']
        digest = entry['sha256']
        if type(size) is not int or size < 0 or size != len(contents[name]):
            raise ValueError(f'manifestのファイルサイズが一致しません: {name}')
        if not isinstance(digest, str) or not re.fullmatch(r'[a-f0-9]{64}', digest) or digest != _digest(contents[name]):
            raise ValueError(f'manifestのファイルSHA-256が一致しません: {name}')
    if seen != set(contents):
        raise ValueError('manifestに不足したファイル記述があります')


def _inspect(path, manifest):
    # Read the current distribution definition at call time, including presets.
    from .assets import asset_specs
    assets = dict(asset_specs())
    expected = set(assets) | {'README.txt', 'SHA256SUMS'}
    if path.is_symlink() or not path.is_file():
        raise ValueError('ZIPは通常ファイルで指定してください')
    if path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError('ZIPのサイズ上限を超えています')
    raw = path.read_bytes()
    if len(raw) > MAX_ARCHIVE_BYTES:
        raise ValueError('ZIPのサイズ上限を超えています')
    archive_hash = _digest(raw)
    manifest_verified = False
    reference = None
    if manifest is not None:
        if manifest.is_symlink() or not manifest.is_file() or manifest.stat().st_size > MAX_MEMBER_BYTES:
            raise ValueError('manifestはサイズ上限内の通常ファイルで指定してください')
        reference = load_json(manifest)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if len(entries) != len(expected) or len(names) != len(set(names)):
            raise ValueError('ZIPのファイル数・重複名が不正です')
        if set(names) != expected:
            raise ValueError('ZIPに許可されていない名前、または不足したファイルがあります')
        if sum(entry.file_size for entry in entries) > MAX_TOTAL_BYTES:
            raise ValueError('ZIPの総展開サイズ上限を超えています')
        for entry in entries:
            mode = entry.external_attr >> 16
            if (entry.orig_filename != entry.filename or entry.is_dir()
                    or stat.S_IFMT(mode) not in (0, stat.S_IFREG)
                    or entry.external_attr & 0x10
                    or '/' in entry.filename or '\\' in entry.filename
                    or entry.flag_bits & 1):
                raise ValueError(f'ZIP内の通常ファイルではありません: {entry.filename}')
            if entry.compress_type != zipfile.ZIP_STORED or entry.compress_size != entry.file_size:
                raise ValueError('この配布形式では無圧縮のZIPメンバーだけを受け付けます')
            if entry.file_size > MAX_MEMBER_BYTES:
                raise ValueError(f'ZIP内ファイルのサイズ上限を超えています: {entry.filename}')
        contents = {entry.filename: archive.read(entry) for entry in entries}
    if manifest is not None:
        _validate_manifest(reference, archive_hash, contents)
        manifest_verified = True
    checksums = {}
    for line in contents['SHA256SUMS'].decode('utf-8').splitlines():
        match = re.fullmatch(r'([a-f0-9]{64})  ([^/\\]+)', line)
        if not match or match[2] in checksums:
            raise ValueError('SHA256SUMSの形式・重複が不正です')
        checksums[match[2]] = match[1]
    if set(checksums) != set(assets):
        raise ValueError('SHA256SUMSの対象ファイルが配布定義と一致しません')
    documents = {}
    for name, samples in assets.items():
        data = contents[name]
        if checksums[name] != _digest(data):
            raise ValueError(f'SHA-256が一致しません: {name}')
        text = data.decode('utf-8')
        result = audit_css(text) if samples is None else audit_html(text, samples=samples)
        if not result['ok']:
            raise ValueError(f'{name}の静的監査に失敗しました: ' + '; '.join(result['errors']))
        if samples is not None:
            documents[name] = text
    links = audit_document_links(documents, assets)
    for name, errors in links.items():
        if errors:
            raise ValueError(f'{name}の参照監査に失敗しました: ' + '; '.join(errors))
    return {'ok': True, 'errors': [], 'sha256': archive_hash,
            'manifest_verified': manifest_verified, 'files': names}


def verify_archive(path, manifest=None):
    """Return an inspection result. No member is ever extracted to the disk."""
    try:
        return _inspect(Path(path), Path(manifest) if manifest is not None else None)
    except (OSError, ValueError, UnicodeError, RuntimeError, NotImplementedError, zipfile.BadZipFile) as error:
        return {'ok': False, 'errors': [str(error)], 'manifest_verified': False, 'files': []}


def main(argv=None):
    parser = argparse.ArgumentParser(description='配布ZIPを展開せず整合性と禁止内容を検査する')
    parser.add_argument('archive', type=Path)
    parser.add_argument('--manifest', type=Path, help='ZIP全体のSHA-256を持つ外部manifest（任意）')
    args = parser.parse_args(argv)
    result = verify_archive(args.archive, args.manifest)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
