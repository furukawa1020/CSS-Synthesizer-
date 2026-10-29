"""Generate repeated HTML. All live input and coordinate calculations stay in CSS."""
from pathlib import Path
import argparse
from html import escape
import re
import shutil
import tempfile
import uuid
import sys
from .source import expand_fragments, compose_css
from .models import load_models, model_tokens, model_styles
from .presets import load_presets, preset_links
from .assets import asset_specs
from .gallery import gallery_html, static_model_selectors
from .comparison import comparison_html, comparison_styles, COMPARISON_COUNTS, comparison_filename

ROOT = Path(__file__).resolve().parents[1]
COUNTS = (96, 192, 384)


def stops(values, initial, formatter, target_prefix=None):
    if target_prefix is not None and not re.fullmatch(r'[a-z][a-z0-9-]*', target_prefix):
        raise ValueError('目盛りのID接頭辞が不正です')
    return '\n'.join(
        f'<span class="tick{" initial" if value == initial else ""}" ' +
        (f'id="{target_prefix}-{index}" tabindex="-1" ' if target_prefix else '') +
        f'style="--tick-index:{index}">{formatter(value)}</span>'
        for index, value in enumerate(values)
    )


def _populate(root, destination):
    template = expand_fragments((root / 'src/page.html').read_text(encoding='utf-8'), root / 'src')
    models = load_models(root / 'src')
    presets = load_presets(root / 'src', {model['id'] for model in models})
    destination.mkdir()
    pages = [('index.html' if count == 192 else f'samples-{count}.html', count, None) for count in COUNTS]
    pages += [(preset['file'], 192, preset) for preset in presets]
    for filename, count, preset in pages:
        state = preset or {'model': 'lissajous', 'k': 3, 'phase': 90, 'amplitude': 80}
        tokens = {
            **model_tokens(models, selected=state['model']),
            '@@INITIAL_VALUES@@': f"--k-raw:{state['k']};--phase-raw:{state['phase']};--amplitude-raw:{state['amplitude'] / 100:g}",
            '@@TIME_AUTO@@': '' if preset else ' checked',
            '@@TIME_PLAY@@': '',
            '@@TIME_STOP@@': ' checked' if preset else '',
            '@@BASELINE_LABEL@@': f"基準値：反復{state['k']:.2f}、位相{state['phase']}°、振幅{state['amplitude']}%。",
            '@@PRESET_LINKS@@': preset_links(presets, preset),
            '@@PRESET_SUMMARY@@': f"{escape(preset['name'])}から開始します。" if preset else '標準の値から開始します。',
            '@@COUNT@@': str(count),
            '@@SAMPLES@@': '\n'.join(
                f'<i class="sample" data-index="{index}" '
                f'style="--index-fallback:{index};--count-fallback:{count}" ></i>'
                for index in range(count)
            ),
            '@@K_STOPS@@': stops(range(1, 9), state['k'], lambda value: f'{value:.2f}', target_prefix='tick-k'),
            '@@PHASE_STOPS@@': stops(range(0, 361, 90), state['phase'], lambda value: f'{value}°', target_prefix='tick-phase'),
            '@@AMPLITUDE_STOPS@@': stops(range(25, 101, 5), state['amplitude'], lambda value: f'{value}%', target_prefix='tick-amplitude'),
            '@@DENSITIES@@': ' / '.join(
                f'<strong aria-current="page">{value}点</strong>' if value == count
                else f'<a href="{"index.html" if value == 192 else f"samples-{value}.html"}">{value}点</a>'
                for value in COUNTS
            ),
        }
        html = template
        for token, replacement in tokens.items():
            html = html.replace(token, replacement)
        if re.search(r'@@[A-Z_]+@@', html):
            raise ValueError('未解決のテンプレートが残っています')
        (destination / filename).write_text(html, encoding='utf-8')
    (destination / 'gallery.html').write_text(gallery_html(presets, models), encoding='utf-8')
    comparison = expand_fragments((root / 'src/compare.html').read_text(encoding='utf-8'), root / 'src')
    parameters = expand_fragments((root / 'src/fragments/parameters.html').read_text(encoding='utf-8'), root / 'src')
    comparison_stops = {
        '@@K_STOPS@@': stops(range(1, 9), 3, lambda value: f'{value:.2f}', target_prefix='tick-k'),
        '@@PHASE_STOPS@@': stops(range(0, 361, 90), 90, lambda value: f'{value}°', target_prefix='tick-phase'),
        '@@AMPLITUDE_STOPS@@': stops(range(25, 101, 5), 80, lambda value: f'{value}%', target_prefix='tick-amplitude'),
    }
    for token, value in comparison_stops.items():
        parameters = parameters.replace(token, value)
    for count in COMPARISON_COUNTS:
        (destination / comparison_filename(count)).write_text(comparison_html(comparison, parameters, models, count), encoding='utf-8')
    for name in ('style.css', 'engine.css'):
        css = compose_css(root / 'src', name)
        if name == 'style.css':
            css += '\n' + model_styles(models) + '\n' + comparison_styles(models)
        (destination / name).write_text(static_model_selectors(css, models), encoding='utf-8')


def build(root=ROOT):
    """Validate a complete candidate before replacing the last successful build.

    The two renames leave a short installation window; this is not an atomic
    directory exchange or a promise of power-loss durability.
    """
    from .audit import audit_directory
    root = Path(root)
    destination = root / 'build'
    if destination.is_symlink() or (destination.exists() and not destination.is_dir()):
        raise ValueError('buildは通常のディレクトリで指定してください')
    with tempfile.TemporaryDirectory(prefix='.build-candidate-', dir=root) as temporary:
        candidate = Path(temporary) / 'build'
        _populate(root, candidate)
        result = audit_directory(candidate, assets=asset_specs(root / 'src'))
        if not result['ok']:
            raise ValueError('生成候補の静的監査に失敗しました: ' + '; '.join(result['errors']))
        previous = root / f'.build-previous-{uuid.uuid4().hex}'
        had_previous = destination.exists()
        if had_previous:
            destination.rename(previous)
        try:
            candidate.rename(destination)
        except OSError:
            if had_previous:
                # The backup is outside the candidate directory, so even a
                # failed rollback cannot be erased by TemporaryDirectory.
                previous.rename(destination)
            raise
        if had_previous:
            shutil.rmtree(previous)
    return destination


def check_build(root=ROOT):
    """Generate and audit a candidate, compare bytes, and leave build untouched."""
    from .audit import audit_directory
    root = Path(root)
    destination = root / 'build'
    errors = []
    try:
        if destination.is_symlink() or not destination.is_dir():
            raise ValueError('比較するbuildディレクトリがありません')
        with tempfile.TemporaryDirectory(prefix='.build-check-', dir=root) as temporary:
            candidate = Path(temporary) / 'build'
            _populate(root, candidate)
            result = audit_directory(candidate, assets=asset_specs(root / 'src'))
            if not result['ok']:
                raise ValueError('生成候補の静的監査に失敗しました: ' + '; '.join(result['errors']))
            expected = {path.name for path in candidate.iterdir()}
            actual = {path.name for path in destination.iterdir()}
            errors.extend(f'buildに不足: {name}' for name in sorted(expected - actual))
            errors.extend(f'buildに余分な項目: {name}' for name in sorted(actual - expected))
            for name in sorted(expected & actual):
                path = destination / name
                if path.is_symlink() or not path.is_file():
                    errors.append(f'buildの通常ファイルではありません: {name}')
                elif path.read_bytes() != (candidate / name).read_bytes():
                    errors.append(f'buildが現在のソースと一致しません: {name}')
    except (OSError, ValueError) as error:
        errors.append(str(error))
    return {'ok': not errors, 'errors': errors}


def main(argv=None):
    parser = argparse.ArgumentParser(description='HTML/CSSを生成または生成結果の鮮度を検査する')
    parser.add_argument('--check', action='store_true', help='既存buildを変更せず現在のソースと比較する')
    args = parser.parse_args(argv)
    if args.check:
        result = check_build(root=ROOT)
        if result['ok']:
            print('buildは現在のソースからの生成結果と一致しています。')
        else:
            for error in result['errors']:
                print(error, file=sys.stderr)
        return 0 if result['ok'] else 1
    try:
        build(root=ROOT)
    except (OSError, ValueError) as error:
        print(f'HTML/CSSを生成できませんでした: {error}', file=sys.stderr)
        return 1
    print('HTML/CSSを生成しました（96 / 192 / 384点）。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
