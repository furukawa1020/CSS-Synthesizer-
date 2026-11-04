"""Portable collections of explicit scenes; never reads browser state."""
from pathlib import Path
import re
from .scene import validate_scene
from .json_data import load_bounded_json

MAX_COLLECTION_BYTES = 64 * 1024
MAX_SCENES = 12


def validate_collection(data):
    if not isinstance(data, dict) or set(data) != {'version', 'title', 'scenes'}:
        raise ValueError('シーン集はversion・title・scenesを指定してください')
    if type(data['version']) is not int or data['version'] != 1:
        raise ValueError('シーン集のversionは1です')
    title = validate_scene(dict(version=1, model='rose', title=data['title']))['title']
    scenes = data['scenes']
    if not isinstance(scenes, list) or not 1 <= len(scenes) <= MAX_SCENES:
        raise ValueError('シーン集は1〜12件です')
    result, seen = [], set()
    for entry in scenes:
        if not isinstance(entry, dict) or set(entry) != {'id', 'scene'}:
            raise ValueError('各シーンはid・sceneを指定してください')
        identifier = entry['id']
        if not isinstance(identifier, str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,47}', identifier) or identifier in seen:
            raise ValueError('シーンidは重複しない英小文字・数字・ハイフン48文字以内です')
        seen.add(identifier)
        result.append(dict(id=identifier, scene=validate_scene(entry['scene'])))
    return dict(version=1, title=title, scenes=result)


def load_collection(path):
    return validate_collection(load_bounded_json(path, MAX_COLLECTION_BYTES))


def export_collection(data, destination):
    """Validate all scenes first; reserve new output and roll back our moves on failure.

    Installation is not a power-loss-safe atomic directory exchange.
    """
    import os
    import shutil
    import tempfile
    from .scene import export_scene
    data = validate_collection(data)
    destination = Path(destination)
    if destination.exists() or destination.is_symlink() or not destination.parent.is_dir():
        raise ValueError('シーン集の出力先は既存の親内の新規フォルダーです')
    with tempfile.TemporaryDirectory(prefix='.collection-candidate-', dir=destination.parent) as folder:
        candidate = Path(folder) / 'output'
        candidate.mkdir()
        for entry in data['scenes']:
            export_scene(entry['scene'], candidate / entry['id'])
        (candidate / 'index.html').write_text(collection_index(data), encoding='utf-8')
        import json
        (candidate / 'collection.json').write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
        write_checksums(candidate)
        destination.mkdir()
        moved = []
        try:
            for path in candidate.iterdir():
                os.replace(path, destination / path.name)
                moved.append(destination / path.name)
        except OSError:
            for path in moved:
                if path.is_dir(): shutil.rmtree(path)
                else: path.unlink()
            destination.rmdir()
            raise
    return destination


def collection_index(data):
    from html import escape
    title = escape(data['title'])
    items = ''.join('<li><a href="' + entry['id'] + '/index.html">' + escape(entry['scene']['title']) + '</a> — ' + escape(entry['scene']['model']) + ' / ' + str(entry['scene']['count']) + '点</li>' for entry in data['scenes'])
    return ('<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'self'; script-src 'none'; style-src 'unsafe-inline'; object-src 'none'; base-uri 'none'\">"
            '<title>' + title + '</title><style>body{font:1rem/1.8 system-ui;margin:2rem auto;padding:0 1rem;max-width:60rem}li{margin:1rem 0}a:focus-visible{outline:3px solid;outline-offset:4px}</style></head><body><main><h1>' + title + '</h1><p>選んだ初期状態から始まる独立したシーン集です。画面内の変更は自動保存されません。各フォルダーのscene.jsonから再生成できます。</p><ol>' + items + '</ol></main></body></html>\n')


def write_checksums(directory):
    """Content checksums detect corruption; they do not authenticate an author."""
    import hashlib
    import json
    directory = Path(directory)
    entries = []
    for path in sorted(directory.rglob('*')):
        if path.is_file() and path.name != 'checksums.json':
            raw = path.read_bytes()
            entries.append(dict(path=path.relative_to(directory).as_posix(), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
    (directory / 'checksums.json').write_text(json.dumps(dict(version=1, files=entries), sort_keys=True, indent=2) + '\n', encoding='utf-8')


def verify_collection(directory):
    import hashlib
    from pathlib import PurePosixPath
    errors, checked, total = [], 0, 0
    try:
        directory = Path(directory)
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError('シーン集は通常のディレクトリで指定してください')
        data = load_collection(directory / 'collection.json')
        expected = {'collection.json', 'index.html'} | {entry['id'] + '/' + name for entry in data['scenes'] for name in ('index.html', 'style.css', 'engine.css', 'scene.json')}
        manifest = load_bounded_json(directory / 'checksums.json', MAX_COLLECTION_BYTES)
        if not isinstance(manifest, dict) or set(manifest) != {'version', 'files'} or type(manifest['version']) is not int or manifest['version'] != 1 or not isinstance(manifest['files'], list) or len(manifest['files']) != len(expected):
            raise ValueError('シーン集のチェックサム形式が不正です')
        actual = set()
        # Only inspect the bounded expected tree, never follow symlink directories.
        for path in directory.iterdir():
            if path.is_symlink(): raise ValueError('シーン集内のsymlinkは検査しません')
            if path.is_dir():
                if path.name not in {entry['id'] for entry in data['scenes']}: raise ValueError('シーン集に余分なディレクトリがあります')
                for child in path.iterdir():
                    if child.is_symlink() or not child.is_file(): raise ValueError('シーン集内に不正な項目があります')
                    actual.add(child.relative_to(directory).as_posix())
            elif path.is_file(): actual.add(path.name)
            else: raise ValueError('シーン集内に通常ファイル以外があります')
        if actual != expected | {'checksums.json'}:
            raise ValueError('シーン集のファイル一覧が一致しません')
        seen = set()
        for entry in manifest['files']:
            if not isinstance(entry, dict) or set(entry) != {'path', 'bytes', 'sha256'}:
                raise ValueError('チェックサムのファイル記述が不正です')
            name = entry['path']
            if not isinstance(name, str) or name not in expected or name in seen or PurePosixPath(name).is_absolute():
                raise ValueError('チェックサムのパスが不正です')
            seen.add(name)
            size, digest = entry['bytes'], entry['sha256']
            if type(size) is not int or not 0 <= size <= 2*1024*1024 or not isinstance(digest, str) or not re.fullmatch(r'[a-f0-9]{64}', digest):
                raise ValueError('チェックサムのサイズ・SHA-256が不正です')
            with (directory / name).open('rb') as stream: raw = stream.read(2*1024*1024+1)
            total += len(raw)
            if total > 32*1024*1024: raise ValueError('シーン集の合計サイズ上限を超えています')
            if len(raw) != size or hashlib.sha256(raw).hexdigest() != digest:
                raise ValueError('内容のチェックサムが一致しません: ' + name)
            checked += 1
        for entry in data['scenes']:
            from .scene import load_scene
            if load_scene(directory / entry['id'] / 'scene.json') != entry['scene']:
                raise ValueError('シーン集と各シーンの初期状態が一致しません')
    except (OSError, ValueError, UnicodeError) as error:
        errors.append(str(error))
    return dict(ok=not errors, errors=errors, checked_files=checked)


def main(argv=None):
    import argparse
    import json
    parser = argparse.ArgumentParser(description='明示JSONから独立シーン集を生成・検査する')
    parser.add_argument('source', type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--output', type=Path, help='新規出力フォルダー')
    mode.add_argument('--check', action='store_true', help='入力manifestだけを検査')
    mode.add_argument('--verify', action='store_true', help='生成済みディレクトリの内容を検査')
    args = parser.parse_args(argv)
    try:
        if args.verify:
            result = verify_collection(args.source)
        else:
            data = load_collection(args.source)
            if args.check:
                result = dict(ok=True, scenes=len(data['scenes']))
            else:
                output = export_collection(data, args.output)
                result = dict(ok=True, output=str(output), scenes=len(data['scenes']))
    except (OSError, ValueError, UnicodeError) as error:
        result = dict(ok=False, errors=[str(error)])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
