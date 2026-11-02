"""Independent normalized-coordinate processing, before view transforms."""
import math

DEFAULTS = dict(swap=False, fold='none', projection='none', gain_x=1, gain_y=1,
                offset_x=0, offset_y=0, quantum=0, bound=False)


def processing_options(value):
    if not isinstance(value, dict):
        return dict(DEFAULTS), ['processingはJSONオブジェクトにしてください']
    errors = []
    options = dict(DEFAULTS)
    if value.keys() - DEFAULTS.keys():
        errors.append('processingに未対応のキーがあります')
    for key, val in value.items():
        if key not in DEFAULTS:
            continue
        if key in ('swap', 'bound'):
            valid = type(val) is bool
        elif key == 'fold':
            valid = isinstance(val, str) and val in ('none', 'x', 'y', 'both')
        elif key == 'projection':
            valid = isinstance(val, str) and val in ('none', 'x', 'y')
        else:
            allowed = (.5, 1, 2) if key.startswith('gain_') else ((-.25, 0, .25) if key.startswith('offset_') else (0, .1, .25, .5))
            valid = type(val) in (int, float) and val in allowed
        if not valid:
            errors.append(f'processing.{key}が対応する値ではありません')
        else:
            options[key] = val
    return options, errors


def process_point(x, y, p):
    if p['swap']:
        x, y = y, x
    if p['fold'] in ('x', 'both'):
        x = abs(x)
    if p['fold'] in ('y', 'both'):
        y = abs(y)
    if p['projection'] == 'x':
        y = 0
    elif p['projection'] == 'y':
        x = 0
    x = x * p['gain_x'] + p['offset_x']
    y = y * p['gain_y'] + p['offset_y']
    if p['quantum']:
        q = p['quantum']
        def nearest(value):
            # Model arithmetic can place a mathematical half-tie a few ulps
            # on either side. Snap only this 1e-12-cell arithmetic boundary;
            # the CSS-pixel geometry tolerance is unchanged.
            scaled = value / q
            lower = math.floor(scaled)
            tie = math.isclose(scaled - lower, .5, rel_tol=0, abs_tol=1e-12)
            return (lower + 1 if tie else math.floor(scaled + .5)) * q
        x, y = nearest(x), nearest(y)
    if p['bound']:
        denominator = max(1, math.hypot(x, y))
        x, y = x / denominator, y / denominator
    return x, y
