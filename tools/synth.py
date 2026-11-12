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
    'synth-pulse.html': ('パルス変調', {'mix': 'amplitude', 'a-cycles': '4', 'b-cycles': '2',
                                       'b-wave': 'square', 'b-duty': '90deg'},
                         '波Bの詳細でパルス幅を25%から75%にすると、波Aが現れる区間が伸びる。'),
    'synth-fold.html': ('折り返す輪郭', {'view': 'polar', 'mix': 'solo-a', 'a-cycles': '5',
                                       'gain': '2', 'shape': 'fold'},
                        '出力の詳細でゲインを200%から100%に下げ、輪郭の折り返しを比べる。'),
}

WAVES = (('sine', 'サイン波'), ('triangle', '三角波'), ('square', '矩形波'), ('saw', 'のこぎり波'))
CYCLES = tuple((f'{n / 2:g}', f'{n / 2:g}周期') for n in range(2, 17))
PHASES = tuple((f'{n}deg', f'{n}°') for n in range(0, 360, 15))
LEVELS = tuple((str(n / 8), f'{n * 12.5:g}%') for n in range(9))
DUTIES = (('90deg', '25%'), ('180deg', '50%'), ('270deg', '75%'))
POLARITIES = (('1', '正'), ('-1', '反転'))

WAVE_FIELDS = (
    ('wave', '波の種類', WAVES), ('cycles', '周期数', CYCLES),
    ('phase', '位相', PHASES), ('level', '振幅', LEVELS),
    ('polarity', '極性', POLARITIES), ('duty', 'パルス幅', DUTIES),
)
MIX = (
    ('sum', '加算ミックス', 'A × (1 − b) + B × b'),
    ('difference', '差分', '(A − B) / 2'),
    ('product', '掛け算', 'A × B'),
    ('amplitude', '振幅変調', 'A × (1 + d × B) / (1 + d)'),
    ('phase', '位相変調', 'Aの位相に 90° × d × B を足す'),
    ('solo-a', '波Aだけ', '波Aを出力へ送る'),
    ('solo-b', '波Bだけ', '波Bを出力へ送る'),
)
VIEWS = (
    ('wave', '波形', '横 = 波の進み · 縦 = 合成波'),
    ('xy', 'XY軌道', '横 = 波A · 縦 = 波B'),
    ('polar', '輪郭', '角度 = 波の進み · 半径 = 合成波'),
)
BALANCES = tuple((str(n / 4), f'A {100 - 25 * n}% ／ B {25 * n}%') for n in range(5))
DEPTHS = tuple((str(n / 4), f'{n * 25}%') for n in range(5))
GAINS = (('0.5', '50%'), ('1', '100%'), ('1.25', '125%'), ('1.5', '150%'), ('2', '200%'))
SHAPES = (('clip', '±1で飽和', '飽和'), ('rectify', '全波整流', '全波整流'),
          ('fold', '折り返し', '折り返し'))
RADII = (('0.4', '小'), ('0.63', '中'), ('0.72', '大'))

TIME_SETTINGS = (
    ('duration', '再生の1周', (('6s', '6秒'), ('12s', '12秒'), ('24s', '24秒'))),
    ('position', '手動の時刻', PHASES),
)

OUTPUT_NUMBERS = (
    ('balance', 'AとBの比率', BALANCES), ('depth', '変調の深さ', DEPTHS),
    ('gain', '出力ゲイン', GAINS), ('radius', '基準半径', RADII),
)

DEFAULTS = {'a-cycles': '2', 'b-cycles': '3', 'mix': 'sum', 'view': 'wave',
            'a-phase': '0deg', 'b-phase': '0deg', 'a-level': '1.0', 'b-level': '1.0',
            'a-wave': 'sine', 'b-wave': 'sine',
            'a-polarity': '1', 'b-polarity': '1', 'a-duty': '180deg', 'b-duty': '180deg',
            'balance': '0.5', 'depth': '1.0', 'gain': '1', 'shape': 'clip', 'radius': '0.63',
            'duration': '12s', 'position': '0deg'}


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
    core = ''.join(select(f'{key}-{name}', label, options, values, prefix=f'{title}の')
                   for name, label, options in WAVE_FIELDS[:4])
    polarity = select(f'{key}-polarity', '極性', POLARITIES, values, prefix=f'{title}の')
    duty = select(f'{key}-duty', 'パルス幅', DUTIES, values, prefix=f'{title}の')
    details = (f'<details class="s-advanced"><summary>{title}の詳細</summary>'
               f'{polarity}<div class="s-pulse-control">{duty}</div></details>')
    return f'<fieldset class="s-wave s-wave-{key}"><legend>{title}</legend>{core}{details}</fieldset>'



def synth_bindings():
    numeric_fields = [(f'{key}-{name}', options) for key in ('a', 'b')
                      for name, _, options in WAVE_FIELDS[1:]]
    numeric_fields.extend((name, options) for name, _, options in (*OUTPUT_NUMBERS, *TIME_SETTINGS))
    lines = [
        f'.synth:has(#s-{key} option[value="{value}"]:checked) {{--s-{key}: {value};}}'
        for key, options in numeric_fields for value, _ in options
    ]
    for group, options in (('mix', MIX), ('view', VIEWS), ('shape', SHAPES)):
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
        **{key.upper(): select(key, label, options, values) for key, label, options in (*OUTPUT_NUMBERS, *TIME_SETTINGS)},
        'SHAPE': select('shape', '出力の加工', SHAPES, values),
        'SHAPE_EQUATION': equations('shape', SHAPES),
        'VIEW': select('view', '描き方', VIEWS, values),
        'WAVE_A': wave_controls('a', values),
        'WAVE_B': wave_controls('b', values),
        'MIX_EQUATION': equations('mix', MIX),
        'VIEW_EQUATION': equations('view', VIEWS),
    }
    for key, value in replacements.items():
        template = template.replace(f'@@{key}@@', value)
    return template
