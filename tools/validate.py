"""Read-only development checks. Unit tests and packaging stay separate."""
import argparse
from pathlib import Path
import sys
from .build import ROOT, check_build
from .source_audit import audit_source
from .audit import audit_directory
from .assets import asset_specs


def evidence_checks(directory):
    from .coordinate_batch import inspect_batch
    from .tangents import inspect_tangent_snapshot
    from .coordinate_batch import inspect_manifest
    from .shared_conditions import inspect_shared_batch
    directory = Path(directory)
    results = []
    try:
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError('観測ディレクトリがありません')
        batches = sorted(directory.glob('batch[0-9]*'))
        for batch in batches:
            if batch.is_symlink() or not batch.is_dir():
                raise ValueError('観測バッチは通常のディレクトリにしてください')
            manifests = []
            for name, inspector in (('index.json', lambda p: inspect_batch(p, require_all=True)),
                                    ('tangents-index.json', lambda p: inspect_manifest(p, lambda data, limit: inspect_tangent_snapshot(data, limit, require_all=True), error_key='max_error_degrees'))):
                path = batch / name
                if path.exists() or path.is_symlink():
                    manifests.append((path, inspector))
            manifests.extend((p, inspect_shared_batch) for p in sorted(batch.glob('shared-*.json')))
            for path, inspector in manifests:
                results.append({'name': path.relative_to(directory).as_posix(), **inspector(path)})
        if not results:
            raise ValueError('照合する観測manifestがありません')
    except (OSError, ValueError, UnicodeError) as error:
        results.append({'name': 'evidence', 'ok': False, 'errors': [str(error)]})
    return results


def validate(root=ROOT):
    root = Path(root)
    checks = []
    for name, operation in (
        ('source', lambda: audit_source(root)),
        ('build', lambda: check_build(root)),
        ('html-css', lambda: audit_directory(root / 'build', assets=asset_specs(root / 'src'))),
    ):
        try:
            result = operation()
        except (OSError, ValueError, UnicodeError) as error:
            result = {'ok': False, 'errors': [str(error)]}
        checks.append({'name': name, **result})
    checks.extend(evidence_checks(root / 'qa/evidence'))
    return {'ok': all(item['ok'] for item in checks), 'checks': checks}


def main(argv=None):
    parser = argparse.ArgumentParser(description='現在のソースと生成物を変更せず検査する')
    args = parser.parse_args(argv)
    result = validate()
    for check in result['checks']:
        print(('PASS ' if check['ok'] else 'FAIL ') + check['name'])
        for error in check.get('errors', []):
            print('  ' + error, file=sys.stderr)
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
