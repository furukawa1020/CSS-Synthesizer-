"""Inspect the current project's source files for JS/TS and Node dependencies.

This is a file inventory guard, not a parser for Python strings or proof that
arbitrary code in another language cannot interpret JavaScript.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SCOPES = ('src', 'tools', 'tests', 'qa', '.github')
EXTENSIONS = {'.js', '.mjs', '.cjs', '.jsx', '.ts', '.tsx', '.mts', '.cts', '.wasm'}
MANIFESTS = {'package.json', 'package-lock.json', 'npm-shrinkwrap.json',
             'pnpm-lock.yaml', 'pnpm-workspace.yaml', 'yarn.lock',
             'bun.lock', 'bun.lockb', 'deno.json', 'deno.jsonc',
             'tsconfig.json', 'jsconfig.json'}


def audit_source(root=ROOT):
    """Inspect root files and implementation scopes without following symlinks.

    Git history, build/dist/tmp output, docs, and qa/local captures are outside
    this inventory. Generated HTML has a separate tools.audit content guard.
    """
    root = Path(root)
    errors = []
    inspected = []

    def inspect(path):
        relative = path.relative_to(root)
        name = path.name.lower()
        if path.is_symlink():
            errors.append(f'ソースのシンボリックリンク: {relative}')
        elif path.is_dir():
            if name == 'node_modules':
                errors.append(f'Node依存ディレクトリ: {relative}')
                return
            if name in {'.git', '__pycache__'} or relative == Path('qa/local'):
                return
            for child in sorted(path.iterdir()):
                inspect(child)
        elif path.is_file():
            inspected.append(relative.as_posix())
            if path.suffix.lower() in EXTENSIONS or name in MANIFESTS:
                errors.append(f'禁止された実装・依存ファイル: {relative}')
        else:
            errors.append(f'通常のソースファイルではありません: {relative}')

    try:
        if root.is_symlink() or not root.is_dir():
            raise ValueError('ソースルートは通常のディレクトリで指定してください')
        for child in sorted(root.iterdir()):
            if child.name in SCOPES or child.name.lower() == 'node_modules' or not child.is_dir():
                if child.name not in {'.git'}:
                    inspect(child)
    except (OSError, ValueError) as error:
        errors.append(str(error))
    return {'ok': not errors, 'errors': errors, 'files': inspected,
            'scopes': ['root files', *SCOPES]}


def main(argv=None):
    parser = argparse.ArgumentParser(description='現在の開発ソースにJS/TS・Node依存を含めない検査')
    parser.add_argument('directory', nargs='?', type=Path, default=ROOT)
    args = parser.parse_args(argv)
    result = audit_source(args.directory)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
