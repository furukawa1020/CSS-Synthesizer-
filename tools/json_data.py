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
    try:
        result = json.loads(text, object_pairs_hook=_object,
                          parse_constant=_constant, parse_float=_float)
    except RecursionError as error:
        raise ValueError('JSONの入れ子が深すぎます') from error
    # Newer Python JSON decoders can parse iteratively. Keep the same bound
    # across Python versions instead of relying solely on RecursionError.
    stack = [iter((result,))]
    while stack:
        try:
            value = next(stack[-1])
        except StopIteration:
            stack.pop()
            continue
        if isinstance(value, (dict, list)):
            if len(stack) > 128:
                raise ValueError('JSONの入れ子が深すぎます')
            stack.append(iter(value.values() if isinstance(value, dict) else value))
    return result


def load_json(path):
    return loads_json(Path(path).read_text(encoding='utf-8'))


def load_bounded_json(path, max_bytes):
    """Read at most limit+1 bytes from a regular file, without following symlinks."""
    if type(max_bytes) is not int or max_bytes < 1:
        raise ValueError('JSONのサイズ上限は正の整数です')
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('JSONは通常ファイルで指定してください')
    with path.open('rb') as stream:
        raw = stream.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ValueError('JSONのサイズ上限を超えています')
    return loads_json(raw.decode('utf-8'))
