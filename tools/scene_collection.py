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
