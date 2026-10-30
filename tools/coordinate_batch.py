"""Inspect an explicit, bounded list of sibling coordinate snapshots."""
from pathlib import Path
import math
import re

from .json_data import loads_json

MAX_MANIFEST_BYTES = 64 * 1024
MAX_SNAPSHOT_BYTES = 2 * 1024 * 1024
MAX_BATCH_BYTES = 16 * 1024 * 1024
MAX_SNAPSHOTS = 256


def _read_bytes(path, limit):
    if path.is_symlink() or not path.is_file():
        raise ValueError(f'通常のJSONファイルではありません: {path.name}')
    if path.stat().st_size > limit:
        raise ValueError(f'JSONのサイズ上限を超えています: {path.name}')
    raw = path.read_bytes()
    if len(raw) > limit:
        raise ValueError(f'JSONのサイズ上限を超えています: {path.name}')
    return raw


def inspect_manifest(manifest, inspector, tolerance=.1, *, error_key="max_error"):
    """Read only flat sibling names; inspect every listed file after validation.

    The explicit list avoids guessing which QA metadata JSON contains points.
    No file or directory is changed, and snapshots are never recursively listed.
    """
    result = {'ok': False, 'checked_files': 0, 'checked_points': 0,
              error_key: 0.0, 'errors': [], 'files': []}
    try:
        if (isinstance(tolerance, bool) or not isinstance(tolerance, (int, float))
                or not math.isfinite(tolerance) or tolerance < 0):
            raise ValueError('許容差は0以上の有限数で指定してください')
        manifest = Path(manifest)
        reference = loads_json(_read_bytes(manifest, MAX_MANIFEST_BYTES).decode('utf-8'))
        if not isinstance(reference, dict) or set(reference) != {'snapshots'}:
            raise ValueError('batch manifestにはsnapshotsだけを指定してください')
        names = reference['snapshots']
        if not isinstance(names, list) or not 1 <= len(names) <= MAX_SNAPSHOTS:
            raise ValueError(f'snapshotsは1〜{MAX_SNAPSHOTS}件の配列にしてください')
        seen = set()
        for name in names:
            if (not isinstance(name, str)
                    or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*\.json', name)
                    or name in seen or name == manifest.name):
                raise ValueError('snapshot名は重複しない同じディレクトリのJSON名にしてください')
            seen.add(name)
    except (OSError, ValueError, UnicodeError, OverflowError) as error:
        result['errors'].append(str(error))
        return result
    total_bytes = 0
    for name in names:
        try:
            remaining = MAX_BATCH_BYTES - total_bytes
            raw = _read_bytes(manifest.parent / name, min(MAX_SNAPSHOT_BYTES, remaining))
            total_bytes += len(raw)
            if total_bytes > MAX_BATCH_BYTES:
                raise ValueError('snapshotの合計サイズ上限を超えています')
            data = loads_json(raw.decode('utf-8'))
            inspection = inspector(data, tolerance)
        except (OSError, ValueError, UnicodeError, OverflowError) as error:
            inspection = {'ok': False, 'checked_points': 0, error_key: 0.0,
                          'errors': [str(error)]}
        result['files'].append({'path': name, **inspection})
        result['checked_files'] += 1
        result['checked_points'] += inspection['checked_points']
        result[error_key] = max(result[error_key], inspection[error_key])
        if not inspection['ok']:
            result['errors'].append(f'{name}の照合に失敗しました')
    result['ok'] = not result['errors']
    return result


def inspect_batch(manifest, tolerance=.1, *, require_all=False):
    """Coordinate adapter; the bounded reader is shared with tangent evidence."""
    from .coordinates import inspect_snapshot
    return inspect_manifest(manifest, lambda data, limit: inspect_snapshot(data, limit, require_all=require_all), tolerance)
