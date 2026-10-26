"""Generate HTML/CSS QA fixtures, never included in the distribution."""
from pathlib import Path
import math
from .build import ROOT

RENDER_GATE = '(container-type: size) and (width: 1cqmin) and (width: calc(sin(1rad) * 1px)) and selector(:has(*))'


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
        write(f'qa-values-{name}.html', html.replace('class="lab"', f'class="lab" style="animation:none;--k-raw:{k};--phase-raw:{phase};--amplitude-raw:{amplitude}"'))
    for name,clock in [('start',0),('end',math.tau)]:
        write(f'qa-loop-{name}.html', html.replace('class="lab"', f'class="lab" style="animation:none;--clock:{clock}"'))


if __name__ == '__main__':
    create_fixtures()
    print('QA専用HTML/CSSを生成しました。CSS分岐のfixtureは実OSや他ブラウザの模擬ではありません。')
