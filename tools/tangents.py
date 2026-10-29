"""Independently check local CSS paint angles against analytic model derivatives."""
import argparse
import json
import math
from pathlib import Path
import sys
from .coordinates import _finite_number

MODELS = {'lissajous', 'wave', 'rose', 'spiral', 'orbit', 'fermat', 'damped-wave', 'standing-wave'}
EPSILON = 1e-6


def tangent_vector(model, u, k, phase_degrees, amplitude, clock):
    """Derivative in mathematical coordinates, up to a positive scalar.

    Fermat uses 2*sqrt(u) times its derivative, continued to u=0 by a
    one-sided limit. Angles are local to a sample, before plot view transforms.
    """
    theta, phase = math.tau * u, math.radians(phase_degrees)
    wave = k * theta + phase + clock
    if model == 'lissajous':
        return amplitude * k * math.cos(wave), 2 * amplitude * math.cos(2 * theta + clock)
    if model == 'wave':
        return 1 / math.pi, amplitude * k * math.cos(wave)
    if model == 'damped-wave':
        return 1 / math.pi, amplitude * math.exp(-3 * u) * (k * math.cos(wave) - 3 / math.tau * math.sin(wave))
    if model == 'standing-wave':
        return 1 / math.pi, amplitude * k * math.cos(k * theta + phase) * math.cos(clock)
    if model == 'rose':
        radius = amplitude * math.sin(k * theta + phase)
        derivative = amplitude * k * math.cos(k * theta + phase)
        angle = theta + clock
        return derivative * math.cos(angle) - radius * math.sin(angle), derivative * math.sin(angle) + radius * math.cos(angle)
    if model in {'spiral', 'fermat'}:
        angle = k * theta + phase + clock
        radius_factor = amplitude * u * k * (2 if model == 'fermat' else 1)
        return amplitude / math.tau * math.cos(angle) - radius_factor * math.sin(angle), amplitude / math.tau * math.sin(angle) + radius_factor * math.cos(angle)
    if model == 'orbit':
        main, secondary = theta + clock, k * theta + phase - clock
        return amplitude * (-.65 * math.sin(main) - .35 * k * math.sin(secondary)), amplitude * (.65 * math.cos(main) - .35 * k * math.cos(secondary))
    raise ValueError('未対応のモデルです')


def tangent_angle(model, u, k, phase_degrees, amplitude, clock):
    dx, dy = tangent_vector(model, u, k, phase_degrees, amplitude, clock)
    return None if math.hypot(dx, dy) < EPSILON else math.degrees(math.atan2(-dy, dx))


def inspect_tangent_snapshot(snapshot, tolerance_degrees=.1):
    errors, checked, maximum = [], 0, 0.0
    tolerance = _finite_number(tolerance_degrees)
    if tolerance is None or tolerance < 0:
        errors.append('方向の許容差は0以上の有限数にしてください')
    if not isinstance(snapshot, dict):
        return {'ok': False, 'errors': errors + ['snapshotはオブジェクトにしてください'], 'checked_points': 0, 'max_error_degrees': 0}
    if not isinstance(snapshot.get('model'), str) or snapshot['model'] not in MODELS:
        errors.append('modelが未対応です')
    values = {}
    for key, low, high in (('k', 1, 8), ('phase_degrees', 0, 360), ('amplitude', .25, 1), ('clock_radians', 0, math.tau + 5e-6)):
        value = _finite_number(snapshot.get(key))
        if value is None or not low <= value <= high:
            errors.append(f'{key}が範囲内の有限数ではありません')
        else:
            values[key] = value
    count = snapshot.get('count')
    if type(count) is not int or count < 2:
        errors.append('countは2以上の整数にしてください')
    points = snapshot.get('tangents')
    if not isinstance(points, list) or not points:
        errors.append('tangentsは空でない観測配列にしてください')
    if not errors:
        seen = set()
        for item in points:
            if not isinstance(item, dict):
                errors.append('方向の観測はオブジェクトにしてください'); continue
            index = item.get('index')
            if type(index) is not int or not 0 <= index < count or index in seen:
                errors.append('方向のindexが不正または重複しています'); continue
            seen.add(index)
            if type(item.get('visible')) is not bool:
                errors.append(f'index={index}のvisibleは真偽値にしてください'); continue
            expected = tangent_angle(snapshot['model'], index / (count - 1), values['k'], values['phase_degrees'], values['amplitude'], values['clock_radians'])
            checked += 1
            if expected is None:
                if item['visible']:
                    errors.append(f'index={index}は接線方向が未定義のため矢印を隠してください')
                continue
            angle = _finite_number(item.get('angle_degrees'))
            if not item['visible'] or angle is None:
                errors.append(f'index={index}は有限の接線方向を表示してください'); continue
            difference = abs((angle - expected + 180) % 360 - 180)
            maximum = max(maximum, difference)
            if difference > tolerance:
                errors.append(f'index={index}の方向誤差{difference:.9g}度が許容差を超えています')
    return {'ok': not errors, 'errors': errors, 'checked_points': checked, 'max_error_degrees': maximum}


def main(argv=None):
    parser = argparse.ArgumentParser(description='接線矢印のローカル角度を独立微分で照合する')
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('--tolerance-degrees', type=float, default=.1)
    args = parser.parse_args(argv)
    try:
        result = inspect_tangent_snapshot(json.loads(args.snapshot.read_text(encoding='utf-8')), args.tolerance_degrees)
    except (OSError, UnicodeError, ValueError) as error:
        result = {'ok': False, 'errors': [str(error)], 'checked_points': 0, 'max_error_degrees': 0}
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
