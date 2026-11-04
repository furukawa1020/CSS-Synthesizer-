"""Small HTML previews of registered starting states, computed at clock zero."""
from html import escape
import math

STARTERS = (('preset-circle.html', 'まる'), ('preset-rose.html', 'はな'),
            ('preset-two-waves.html', 'なみ'), ('preset-spiral.html', 'うず'))


def starter_points(preset):
    points = []
    a, k, phase = preset['amplitude']/100, preset['k'], math.radians(preset['phase'])
    for i in range(48):
        u = i/47
        theta = math.tau*u
        if preset['model'] == 'lissajous':
            x, y = a*math.sin(k*theta+phase), a*math.sin(2*theta)
        elif preset['model'] == 'wave':
            x, y = 2*u-1, a*math.sin(k*theta+phase)
        elif preset['model'] == 'rose':
            radius = a*math.sin(k*theta+phase)
            x, y = radius*math.cos(theta), radius*math.sin(theta)
        elif preset['model'] == 'spiral':
            x, y = a*u*math.cos(k*theta+phase), a*u*math.sin(k*theta+phase)
        else:
            raise ValueError('開始プレビューに未対応のモデルです')
        points.append((50+44*x, 50-44*y))
    return points


def starter_links(presets, selected=None):
    available = {p['file']:p for p in presets}
    links = []
    for filename, label in STARTERS:
        preset = available.get(filename)
        if preset is None or preset['model'] not in ('lissajous', 'wave', 'rose', 'spiral'):
            continue
        dots = ''.join(f'<i style="left:{x:.1f}%;top:{y:.1f}%"></i>' for x,y in starter_points(preset))
        current = ' aria-current="page"' if selected and selected['file'] == filename else ''
        links.append(f'<a href="{filename}"{current}><span class="starter-art" aria-hidden="true">{dots}</span><span>{label}</span></a>')
    return '<nav class="starter-links" aria-label="絵から遊び始める">' + ''.join(links) + '</nav>'
