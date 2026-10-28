"""Strict JSON for the project's declarative model and preset data."""
import json
import math
from pathlib import Path


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'JSONのキーが重複しています: {key}')
        result[key] = value
    return result


def _constant(value):
    raise ValueError(f'JSONに有限数でない値は指定できません: {value}')


def _float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f'JSONの数値が有限数の範囲を超えています: {value}')
    return number


def loads_json(text):
    """Reject duplicate object keys and non-finite numeric extensions."""
    return json.loads(text, object_pairs_hook=_object,
                      parse_constant=_constant, parse_float=_float)


def load_json(path):
    return loads_json(Path(path).read_text(encoding='utf-8'))
