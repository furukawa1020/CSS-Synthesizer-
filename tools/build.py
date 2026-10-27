"""Generate repeated HTML. All live input and coordinate calculations stay in CSS."""
from pathlib import Path
from html import escape
import re
import shutil
import tempfile
import uuid
from .source import expand_fragments, compose_css
from .models import load_models, model_tokens, model_styles
from .presets import PRESET_FILENAMES, load_presets, preset_links

ROOT = Path(__file__).resolve().parents[1]
COUNTS = (96, 192, 384)
ASSETS = ('index.html', 'samples-96.html', 'samples-384.html', 'style.css', 'engine.css', *PRESET_FILENAMES)


def stops(values, initial, formatter):
    return '\n'.join(
        f'<span class="tick{" initial" if value == initial else ""}" '
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
            '@@K_STOPS@@': stops(range(1, 9), state['k'], lambda value: f'{value:.2f}'),
            '@@PHASE_STOPS@@': stops(range(0, 361, 90), state['phase'], lambda value: f'{value}°'),
            '@@AMPLITUDE_STOPS@@': stops(range(25, 101, 5), state['amplitude'], lambda value: f'{value}%'),
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
    for name in ('style.css', 'engine.css'):
        css = compose_css(root / 'src', name)
        if name == 'style.css':
            css += '\n' + model_styles(models)
        (destination / name).write_text(css, encoding='utf-8')


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
        result = audit_directory(candidate)
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


if __name__ == '__main__':
    build()
    print('HTML/CSSを生成しました（96 / 192 / 384点）。')
