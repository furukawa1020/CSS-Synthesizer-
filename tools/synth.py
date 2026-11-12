"""Generate the native controls and sample markup for the CSS synthesizer."""
from html import escape

SAMPLE_COUNT = 192
PATCHES = {
    'index.html': ('重ねる', {}, '波Bの位相や周期を変えて、二つの波を重ねてみる。'),
    'synth-cancel.html': ('相殺', {'mix': 'difference', 'a-cycles': '2', 'b-cycles': '2'},
                          '同じ波を引くと中央線。波Bの位相を90°にすると波が現れる。'),
    'synth-xy.html': ('XYの円', {'view': 'xy', 'a-cycles': '2', 'b-cycles': '2', 'b-phase': '90deg'},
                      '位相差90°で円。波Bを0°にすると線、3周期にすると別の軌道になる。'),
    'synth-polar.html': ('波の輪郭', {'view': 'polar', 'a-cycles': '3', 'b-cycles': '5'},
                         '合成波を円の半径へ送る。周期や混ぜ方を変えると輪郭が変わる。'),
}

WAVES = (('sine', 'サイン波'), ('triangle', '三角波'), ('square', '矩形波'), ('saw', 'のこぎり波'))
CYCLES = tuple((str(n), f'{n}周期') for n in range(1, 9))
PHASES = tuple((f'{n}deg', f'{n}°') for n in (0, 90, 180, 270))
LEVELS = tuple((str(n / 100), f'{n}%') for n in (0, 25, 50, 75, 100))
MIX = (
    ('sum', '平均', '(A + B) / 2'),
    ('difference', '差分', '(A − B) / 2'),
    ('product', '掛け算', 'A × B'),
    ('amplitude', '振幅変調', 'A × (1 + B) / 2'),
    ('phase', '位相変調', 'Aの位相に 90° × B を足す'),
)
VIEWS = (
    ('wave', '波形', '横 = 波の進み · 縦 = 合成波'),
    ('xy', 'XY軌道', '横 = 波A · 縦 = 波B'),
    ('polar', '輪郭', '角度 = 波の進み · 半径 = 合成波'),
)
DEFAULTS = {'a-cycles': '2', 'b-cycles': '3', 'mix': 'sum', 'view': 'wave',
            'a-phase': '0deg', 'b-phase': '0deg', 'a-level': '1.0', 'b-level': '1.0',
            'a-wave': 'sine', 'b-wave': 'sine'}


def select(key, label, options, values, *, prefix=''):
    items = []
    for value, text, *_ in options:
        selected = ' selected' if value == values[key] else ''
        items.append(f'<option value="{value}"{selected}>{text}</option>')
    return (f'<label class="s-control" for="s-{key}"><span>{label}</span>'
            f'<select id="s-{key}" name="{key}" aria-label="{prefix}{label}">'
            + ''.join(items) + '</select></label>')


def wave_controls(key, values):
    title = f'波{key.upper()}'
    controls = ''.join(select(f'{key}-{name}', label, options, values, prefix=f'{title}の')
                       for name, label, options in (
                           ('wave', '波の種類', WAVES), ('cycles', '周期数', CYCLES),
                           ('phase', '位相', PHASES), ('level', '振幅', LEVELS),
                       ))
    return f'<fieldset class="s-wave s-wave-{key}"><legend>{title}</legend>{controls}</fieldset>'


def synth_bindings():
    lines = []
    for key in ('a', 'b'):
        for name, options in (('cycles', CYCLES), ('phase', PHASES), ('level', LEVELS)):
            for value, _ in options:
                lines.append(f'.synth:has(#s-{key}-{name} option[value="{value}"]:checked)'
                             f' {{--s-{key}-{name}: {value};}}')
    for group, options in (('mix', MIX), ('view', VIEWS)):
        for value, _, _ in options:
            lines.append(f'.synth:has(#s-{group} option[value="{value}"]:checked)'
                         f' [data-{group}="{value}"] {{display: inline;}}')
    return '\n'.join(lines)


def trace(channel):
    class_name = 'sample s-dot' if channel == 'out' else 's-dot'
    points = ''.join(f'<i class="{class_name}" style="--s-i:{i}"></i>'
                     for i in range(SAMPLE_COUNT))
    return f'<div class="s-trace s-trace-{channel}">{points}</div>'


def equations(group, options):
    return ''.join(f'<span data-{group}="{value}">{escape(formula)}</span>'
                   for value, _, formula in options)


def synth_html(template, filename):
    _, settings, instruction = PATCHES[filename]
    values = DEFAULTS | settings
    links = ' '.join(
        '<a href="{}"{}>{}</a>'.format(page, ' aria-current="page"' if page == filename else '', label)
        for page, (label, _, _) in PATCHES.items()
    )
    replacements = {
        'PATCH_LINKS': links,
        'INSTRUCTION': escape(instruction),
        'SAMPLE_INTERVALS': str(SAMPLE_COUNT - 1),
        'TRACES': ''.join(trace(channel) for channel in ('a', 'b', 'out')),
        'MIX': select('mix', '混ぜ方', MIX, values),
        'VIEW': select('view', '描き方', VIEWS, values),
        'WAVE_A': wave_controls('a', values),
        'WAVE_B': wave_controls('b', values),
        'MIX_EQUATION': equations('mix', MIX),
        'VIEW_EQUATION': equations('view', VIEWS),
    }
    for key, value in replacements.items():
        template = template.replace(f'@@{key}@@', value)
    return template
