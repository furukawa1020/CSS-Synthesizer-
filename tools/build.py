"""Generate repeated HTML. All live input and coordinate calculations stay in CSS."""
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
COUNTS = (96, 192, 384)
ASSETS = ('index.html', 'samples-96.html', 'samples-384.html', 'style.css', 'engine.css')


def stops(values, initial, formatter):
    return '\n'.join(
        f'<span class="tick{" initial" if value == initial else ""}" '
        f'style="--tick-index:{index}">{formatter(value)}</span>'
        for index, value in enumerate(values)
    )


def build(root=ROOT):
    root = Path(root)
    destination = root / 'build'
    template = (root / 'src/page.html').read_text(encoding='utf-8')
    if destination.is_symlink():
        raise ValueError('buildはシンボリックリンクにできません')
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir()
    for count in COUNTS:
        tokens = {
            '@@COUNT@@': str(count),
            '@@SAMPLES@@': '\n'.join(
                f'<i class="sample" data-index="{index}" '
                f'style="--index-fallback:{index};--count-fallback:{count}" ></i>'
                for index in range(count)
            ),
            '@@K_STOPS@@': stops(range(1, 9), 3, lambda value: f'{value:.2f}'),
            '@@PHASE_STOPS@@': stops(range(0, 361, 90), 90, lambda value: f'{value}°'),
            '@@AMPLITUDE_STOPS@@': stops(range(25, 101, 5), 80, lambda value: f'{value}%'),
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
        filename = 'index.html' if count == 192 else f'samples-{count}.html'
        (destination / filename).write_text(html, encoding='utf-8')
    for name in ('style.css', 'engine.css'):
        shutil.copyfile(root / 'src' / name, destination / name)
    return destination


if __name__ == '__main__':
    build()
    print('HTML/CSSを生成しました（96 / 192 / 384点）。')
