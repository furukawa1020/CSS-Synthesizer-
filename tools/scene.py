"""Compile explicit JSON starting states; no browser state is read or saved."""
from pathlib import Path
from decimal import Decimal
import math
from .build import ROOT
from .json_data import loads_json
from .models import load_models

MAX_SCENE_BYTES = 16 * 1024
FIELDS = {'version', 'model', 'k', 'phase', 'amplitude', 'count'}


def validate_scene(data, source=ROOT / 'src'):
    if not isinstance(data, dict) or set(data) - FIELDS:
        raise ValueError('sceneは許可されたキーだけのJSONオブジェクトにしてください')
    if type(data.get('version')) is not int or data['version'] != 1:
        raise ValueError('sceneのversionは1です')
    model = data.get('model')
    if not isinstance(model, str) or model not in {m['id'] for m in load_models(source)}:
        raise ValueError('sceneのmodelが未対応です')
    result = dict(version=1, model=model, k=data.get('k', 3), phase=data.get('phase', 90),
                  amplitude=data.get('amplitude', 80), count=data.get('count', 192))
    if type(result['count']) is not int or result['count'] not in (96, 192, 384):
        raise ValueError('countは96/192/384です')
    for key, low, high, scale in (('k', 1, 8, 100), ('phase', 0, 360, 1), ('amplitude', 25, 100, 1)):
        value = result[key]
        if (type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high
                or Decimal(str(value)) * scale != (Decimal(str(value)) * scale).to_integral_value()):
            raise ValueError(f'{key}は範囲内の対応する精度で指定してください')
        result[key] = float(value) if key == 'k' else int(value)
    return result


def load_scene(path, source=ROOT / 'src'):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('sceneは通常のJSONファイルにしてください')
    with path.open('rb') as stream:
        raw = stream.read(MAX_SCENE_BYTES + 1)
    if len(raw) > MAX_SCENE_BYTES:
        raise ValueError('sceneは16KiB以下にしてください')
    return validate_scene(loads_json(raw.decode('utf-8')), source)
