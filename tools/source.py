"""Compose repository-native HTML fragments and CSS without browser code."""
from pathlib import Path
import re

FRAGMENT = re.compile(r'@@FRAGMENT:([^@]*)@@')


def expand_fragments(text, source, trail=()):
    directory = Path(source) / 'fragments'
    if directory.is_symlink():
        raise ValueError('HTML断片ディレクトリはシンボリックリンクにできません')
    def replace(match):
        name = match.group(1)
        if not re.fullmatch(r'[a-z][a-z0-9-]*', name):
            raise ValueError(f'不正なHTML断片名: {name}')
        if name in trail:
            raise ValueError(f'循環したHTML断片: {name}')
        path = directory / f'{name}.html'
        if path.is_symlink() or not path.is_file():
            raise ValueError(f'HTML断片が見つかりません: {name}')
        return expand_fragments(path.read_text(encoding='utf-8'), source, (*trail, name))
    expanded = FRAGMENT.sub(replace, text)
    if '@@FRAGMENT:' in expanded:
        raise ValueError('不正なHTML断片トークンが残っています')
    return expanded


def compose_css(source, name):
    source = Path(source)
    parts = [source / name]
    directory = source / ('styles' if name == 'style.css' else 'engines')
    if directory.is_symlink():
        raise ValueError('CSS拡張ディレクトリはシンボリックリンクにできません')
    if directory.exists():
        parts.extend(sorted(directory.glob('*.css')))
    if any(path.is_symlink() or not path.is_file() for path in parts):
        raise ValueError('CSSは通常ファイルで指定してください')
    return '\n'.join(path.read_text(encoding='utf-8') for path in parts)
