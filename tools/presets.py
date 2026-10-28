"""Validated starting states for self-contained, script-free HTML pages."""
from html import escape
import re
from pathlib import Path
from .json_data import load_json

MAX_PRESETS = 24
DEFAULT_MODEL_IDS = ('lissajous', 'wave', 'rose', 'spiral', 'orbit')


def validate_presets(presets, model_ids=DEFAULT_MODEL_IDS):
    if not isinstance(presets, list) or not 1 <= len(presets) <= MAX_PRESETS:
        raise ValueError('プリセットは1〜24ページの配列にしてください')
    seen = set()
    names = set()
    for preset in presets:
        if not isinstance(preset, dict):
            raise ValueError('プリセットはオブジェクトにしてください')
        filename = preset.get('file')
        if not isinstance(filename, str) or not re.fullmatch(r'preset-[a-z0-9]+(?:-[a-z0-9]+)*\.html', filename) or filename in seen:
            raise ValueError('プリセットのページ名が不正または重複しています')
        seen.add(filename)
        if not isinstance(preset.get('name'), str) or not preset['name'].strip() or preset['name'].strip() in names:
            raise ValueError('プリセット名は空でなく一意にしてください')
        names.add(preset['name'].strip())
        if not isinstance(preset.get('model'), str) or preset['model'] not in model_ids:
            raise ValueError('プリセットのモデルが定義されていません')
        for key, low, high, step in (('k', 1, 8, 1), ('phase', 0, 360, 90), ('amplitude', 25, 100, 5)):
            value = preset.get(key)
            if type(value) is not int or not low <= value <= high or value % step:
                raise ValueError(f'プリセットの{key}は対応する初期目盛りに合わせてください')
    return presets


def load_presets(source, model_ids=None):
    source = Path(source)
    if model_ids is None:
        from .models import load_models
        model_ids = {model['id'] for model in load_models(source)}
    return validate_presets(load_json(source / 'presets.json'), model_ids)


def preset_links(presets, selected=None):
    links = ['<a href="index.html">標準の画面<span>192点・自動再生</span></a>']
    for preset in presets:
        current = ' aria-current="page"' if selected and preset['file'] == selected['file'] else ''
        links.append(
            f'<a href="{preset["file"]}"{current}>{escape(preset["name"])}'
            f'<span>{preset["k"]:.2f} / {preset["phase"]}° / {preset["amplitude"]}%・停止</span></a>'
        )
    return '\n'.join(links)
