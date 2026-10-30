"""Generate HTML/CSS QA fixtures, never included in the distribution."""
from pathlib import Path
import math
import re
from .build import ROOT

RENDER_GATE = '(container-type: size) and (width: 1cqmin) and (width: calc(sin(1rad) * 1px)) and selector(:has(*))'


def _lab_style(html, declarations):
    """Append to the existing main style instead of creating duplicate attributes."""
    return re.sub(r'(<main class="lab" style=")([^"]*)(")',
                  lambda match: match[1] + match[2] + ';' + declarations + match[3], html, count=1)


def create_fixtures(directory=ROOT / 'build'):
    directory = Path(directory)
    html = (directory / 'index.html').read_text(encoding='utf-8')
    style = (directory / 'style.css').read_text(encoding='utf-8')
    engine = (directory / 'engine.css').read_text(encoding='utf-8')
    def write(name, content):
        (directory / name).write_text(content, encoding='utf-8')
    write('qa-square.html', html.replace('class="stage"', 'class="stage" style="inline-size:500px;block-size:500px;flex:none"'))
    write('qa-frames.html', '<!doctype html><html lang="ja"><meta charset="utf-8"><title>描画領域の検証</title><iframe title="portrait" src="index.html" width="360" height="900"></iframe><iframe title="landscape" src="index.html" width="800" height="800"></iframe></html>')
    write('qa-layouts.html', '<!doctype html><html lang="ja"><meta charset="utf-8"><title>幅ごとの表示検証</title><style>body{margin:16px;font:16px system-ui}iframe{display:block;border:0;margin:12px 0 32px}</style><h1>幅ごとの表示検証</h1><p>iframeでの確認。実機タッチの検証ではありません。</p>' + ''.join(f'<h2>{width}px</h2><iframe title="width-{width}" src="index.html" width="{width}" height="1700"></iframe>' for width in (360,390,768,1280,1440)) + '</html>')
    write('qa-reduced-style.css', style.replace('@media (prefers-reduced-motion: reduce)', '@media all'))
    write('qa-reduced-engine.css', engine.replace('@media (prefers-reduced-motion: reduce)', '@media all'))
    write('qa-reduced.html', html.replace('href="style.css"', 'href="qa-reduced-style.css"').replace('href="engine.css"', 'href="qa-reduced-engine.css"'))
    write('qa-no-render.css', style.replace(f'@supports not ({RENDER_GATE})', '@supports (display: block)'))
    write('qa-no-render.html', html.replace('href="style.css"', 'href="qa-no-render.css"'))
    write('qa-text-200.html', html.replace('</head>', '<style>html{font-size:200%}</style></head>'))
    for name, source in [('mobile','index.html'),('large-text','qa-text-200.html'),('fallback','qa-no-render.html')]:
        write(f'qa-{name}-frames.html', f'<!doctype html><html lang="ja"><meta charset="utf-8"><title>{name}の表示検証</title><style>body{{margin:0}}iframe{{border:0;display:block}}</style><iframe title="{name}-360" src="{source}" width="360" height="900"></iframe><iframe title="{name}-1280" src="{source}" width="1280" height="900"></iframe></html>')
    for name,k,phase,amplitude in [('fraction',3.09,89.6,.795),('carry',3.999,359.9,.999),('upper',8,360,1)]:
        write(f'qa-values-{name}.html', _lab_style(html, f'animation:none;--k-raw:{k};--phase-raw:{phase};--amplitude-raw:{amplitude}'))
    for name,clock in [('start',0),('end',math.tau)]:
        write(f'qa-loop-{name}.html', _lab_style(html, f'animation:none;--clock:{clock}'))


def create_comparison_fixtures(directory=ROOT / 'build'):
    """Bounded fixtures for the comparison, transformed points and native UI."""
    directory = Path(directory)
    html = (directory / 'index.html').read_text(encoding='utf-8')
    style = (directory / 'style.css').read_text(encoding='utf-8')
    def write(name, value):
        (directory / name).write_text(value, encoding='utf-8')
    # 97 samples include u=1/8,3/8,5/8,7/8 exactly. For k=2, phi=t=0,
    # both Lissajous derivatives vanish there; no lossy pi/2 clock is needed.
    samples = ''.join(f'<i class="sample" data-index="{i}" style="--index-fallback:{i};--count-fallback:97"></i>' for i in range(97))
    zero = re.sub(r'(<div class="plot" aria-hidden="true">).*?(</div>)',
                  lambda match: match[1] + samples + match[2], html, flags=re.S)
    zero = _lab_style(zero, 'animation:none;--clock:0;--k-raw:2;--phase-raw:0')
    write('qa-tangent-zero.html', zero.replace('192 点', '97 点（検証用）'))
    write('qa-print-style.css', style.replace('@media print', '@media all').replace('@media screen', '@media not all'))
    comparison = (directory / 'compare.html').read_text(encoding='utf-8').replace('href="style.css"', 'href="qa-print-style.css"')
    def print_choice(match):
        tag = re.sub(r'\schecked(?=[\s>])', '', match[0])
        identifier = re.search(r'id="([^"]+)"', tag)[1]
        return tag[:-1] + ' checked>' if identifier in {'compare-rose', 'compare-fermat'} else tag
    comparison = re.sub(r'<input[^>]*id="compare-[^"]+"[^>]*>', print_choice, comparison)
    write('qa-comparison-print.html', comparison)
    write('qa-rad-fallback-style.css', style.replace('@supports (counter-reset: probe round(down, 1.5, 1) remainder mod(3, 2))', '@supports not (display: block)'))
    fallback = html.replace('href="style.css"', 'href="qa-rad-fallback-style.css"')
    def rad_choice(match):
        tag = re.sub(r'\schecked(?=[\s>])', '', match[0])
        return tag[:-1] + ' checked>' if 'id="phase-unit-rad"' in tag else tag
    fallback = re.sub(r'<input[^>]*name="phase-unit"[^>]*>', rad_choice, fallback)
    write('qa-rad-fallback.html', fallback)
    for name, source in [('compare', 'compare.html'), ('text200', 'qa-text-200.html'), ('features', 'features.html')]:
        write(f'qa-{name}-frames.html', f'<!doctype html><html lang="ja"><meta charset="utf-8"><title>幅の確認</title><style>body{{margin:0}}iframe{{border:0;display:block}}</style><iframe title="test-360" src="{source}" width="360" height="900"></iframe><iframe title="test-1280" src="{source}" width="1280" height="900"></iframe></html>')


def create_batch80_fixtures(directory=ROOT / 'build'):
    """Comparison width, text, and CSS-media branches; not real OS settings."""
    directory = Path(directory)
    html = (directory / 'compare.html').read_text(encoding='utf-8')
    style = (directory / 'style.css').read_text(encoding='utf-8')
    def write(name, value):
        (directory / name).write_text(value, encoding='utf-8')
    def choices(value):
        groups = {'opacity', 'sample-range', 'point-shape', 'clock-period', 'clock-direction'}
        selected = {'opacity-quarter', 'range-half', 'shape-arrow', 'period-48', 'direction-reverse'}
        def replace(match):
            tag = match[0]
            group = re.search(r'name="([^"]+)"', tag)
            if not group or group[1] not in groups:
                return tag
            tag = re.sub(r'\schecked(?=[\s>])', '', tag)
            identifier = re.search(r'id="([^"]+)"', tag)[1]
            return tag[:-1] + ' checked>' if identifier in selected else tag
        return re.sub(r'<input[^>]*>', replace, value)
    write('qa-compare-text200.html', html.replace('</head>', '<style>html{font-size:200%}</style></head>'))
    write('qa-batch80-layouts.html', '<!doctype html><html lang="ja"><meta charset="utf-8"><title>比較の幅と文字拡大</title><style>body{margin:0}iframe{display:block;border:0}</style>' + ''.join(f'<iframe title="{name}-{width}" src="{name}.html" width="{width}" height="1000"></iframe>' for name,width in [('compare',360),('compare',1280),('qa-compare-text200',360),('gallery',360)]) + '</html>')
    printed = (directory / 'qa-comparison-print.html').read_text(encoding='utf-8')
    write('qa-batch80-print.html', choices(printed))
    forced = style.replace('@media not (forced-colors: active)', '@media not all').replace('@media (forced-colors: active)', '@media all')
    write('qa-batch80-forced.css', forced)
    write('qa-batch80-forced.html', choices(html).replace('href="style.css"', 'href="qa-batch80-forced.css"'))


if __name__ == '__main__':
    create_fixtures()
    create_comparison_fixtures()
    create_batch80_fixtures()
    print('QA専用HTML/CSSを生成しました。CSS分岐のfixtureは実OSや他ブラウザの模擬ではありません。')
