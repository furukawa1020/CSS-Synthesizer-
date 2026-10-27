"""Validated starting states for self-contained, script-free HTML pages."""
from html import escape
import json
from pathlib import Path

PRESET_FILENAMES = (
    'preset-circle.html', 'preset-weave.html',
    'preset-two-waves.html', 'preset-fine-wave.html',
)


def validate_presets(presets, model_ids=('lissajous', 'wave')):
    if not isinstance(presets, list) or len(presets) != len(PRESET_FILENAMES):
        raise ValueError('プリセットは定義済み4ページの配列にしてください')
    seen = set()
    for preset in presets:
        if not isinstance(preset, dict):
            raise ValueError('プリセットはオブジェクトにしてください')
        filename = preset.get('file')
        if not isinstance(filename, str) or filename not in PRESET_FILENAMES or filename in seen:
            raise ValueError('プリセットのページ名が不正または重複しています')
        seen.add(filename)
        if not isinstance(preset.get('name'), str) or not preset['name'].strip():
            raise ValueError('プリセット名が必要です')
        if not isinstance(preset.get('model'), str) or preset['model'] not in model_ids:
            raise ValueError('プリセットのモデルが定義されていません')
        for key, low, high, step in (('k', 1, 8, 1), ('phase', 0, 360, 90), ('amplitude', 25, 100, 5)):
            value = preset.get(key)
            if type(value) is not int or not low <= value <= high or value % step:
                raise ValueError(f'プリセットの{key}は対応する初期目盛りに合わせてください')
    return presets


def load_presets(source, model_ids=('lissajous', 'wave')):
    return validate_presets(json.loads((Path(source) / 'presets.json').read_text(encoding='utf-8')), model_ids)


def preset_links(presets, selected=None):
    links = ['<a href="index.html">標準の画面<span>192点・自動再生</span></a>']
    for preset in presets:
        current = ' aria-current="page"' if selected and preset['file'] == selected['file'] else ''
        links.append(
            f'<a href="{preset["file"]}"{current}>{escape(preset["name"])}'
            f'<span>{preset["k"]:.2f} / {preset["phase"]}° / {preset["amplitude"]}%・停止</span></a>'
        )
    return '\n'.join(links)
