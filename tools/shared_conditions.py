"""Validate shared comparison conditions as well as independent geometry."""
import argparse
import json
from pathlib import Path
from .coordinate_batch import inspect_manifest
from .coordinates import inspect_snapshot


def inspect_shared_batch(manifest, tolerance=.1):
    baseline = None
    models = set()
    required = ('k', 'phase_degrees', 'amplitude', 'clock_radians', 'count')
    from .processing import DEFAULTS, processing_options
    defaults = {'mirror_x': False, 'mirror_y': False, 'rotation_degrees': 0, 'plot_scale': 1}
    def inspect(data, limit):
        nonlocal baseline
        result = inspect_snapshot(data, limit, require_all=True)
        if not result['ok']:
            return result
        conditions = tuple(data[key] for key in required) + tuple(data.get(key, value) for key, value in defaults.items())
        options, _ = processing_options(data.get('processing', {}))
        conditions += tuple(options[key] for key in DEFAULTS)
        if baseline is None:
            baseline = conditions
        elif conditions != baseline:
            result['errors'].append('比較図の入力・時計・点数・表示変換が共有条件と一致しません')
        if data['model'] in models:
            result['errors'].append('比較するモデルが重複しています')
        models.add(data['model'])
        result['ok'] = not result['errors']
        return result
    result = inspect_manifest(manifest, inspect, tolerance)
    if result['checked_files'] < 2:
        result['errors'].append('共有条件の検査には2モデル以上の観測が必要です')
    result['ok'] = not result['errors']
    result['models'] = sorted(models)
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description='比較図の全点座標と共有条件を照合する')
    parser.add_argument('manifest',type=Path)
    parser.add_argument('--tolerance',type=float,default=.1)
    args=parser.parse_args(argv)
    result=inspect_shared_batch(args.manifest,args.tolerance)
    print(json.dumps(result,ensure_ascii=False,allow_nan=False,indent=2))
    return 0 if result['ok'] else 1


if __name__=='__main__':
    raise SystemExit(main())
