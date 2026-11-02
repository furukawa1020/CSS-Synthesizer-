"""Read-only development checks. Unit tests and packaging stay separate."""
import argparse
from pathlib import Path
import sys
from .build import ROOT, check_build
from .source_audit import audit_source
from .audit import audit_directory
from .assets import asset_specs


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
