"""DOMで観測した点の中心を、独立した数式でCSS px単位に照合する。"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys


# 2π may be serialized as 6.28319 by a browser's computed-style API.
# Keep this radian allowance separate from the coordinate tolerance in CSS px.
_CLOCK_SERIALIZATION_MARGIN = 5e-6
SUPPORTED_MODELS = frozenset({"lissajous", "wave", "rose", "spiral", "orbit", "fermat", "damped-wave", "standing-wave"})


def _result(errors: list[str], checked: int = 0, maximum: float = 0.0) -> dict:
    return {
        "ok": not errors,
        "max_error": maximum,
        "checked_points": checked,
        "errors": errors,
    }


def _finite_number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        number = float(value)
    except (OverflowError, ValueError):
        return None
    return number if math.isfinite(number) else None


def inspect_snapshot(snapshot: dict, tolerance: float = 0.1) -> dict:
    """観測snapshotを検査する。CSSの--x/--yを期待値には使用しない。

    pointsのx/yはビューポートにおけるDOM点の中心、stageのx/yは
    同じ座標系の描画領域左上。max_errorは点中心間の距離（CSS px）。
    clock_radiansの上端だけは数値シリアライズ用に5e-6 radまで許容し、
    照合にはクランプせず観測値を使う。座標の許容差は緩めない。
    mirror_x・mirror_yは任意の真偽値で、省略時はfalse。表示反転だけを検査する。
    rotation_degreesは数理座標で反時計回りを正とし、反転後に適用する。省略時0。
    plot_scaleは表示倍率0.5・0.75・1。省略時1。数式Aとは別に適用する。
    不正な入力はok:falseと日本語errorsを返す。
    """
    errors: list[str] = []
    limit = _finite_number(tolerance)
    if limit is None or limit < 0:
        errors.append("許容差は0以上の有限数で指定してください")
    if not isinstance(snapshot, dict):
        return _result(errors + ["snapshotはJSONオブジェクトで指定してください"])

    model = snapshot.get("model")
    if not isinstance(model, str) or model not in SUPPORTED_MODELS:
        errors.append("modelはlissajous・wave・rose・spiral・orbit・fermat・damped-wave・standing-waveで指定してください")
    values = {}
    for key, lower, upper in (
        ("k", 1, 8),
        ("phase_degrees", 0, 360),
        ("amplitude", .25, 1),
        ("clock_radians", 0, math.tau + _CLOCK_SERIALIZATION_MARGIN),
    ):
        value = _finite_number(snapshot.get(key))
        if value is None or not lower <= value <= upper:
            errors.append(f"{key}は{lower}〜{upper}の有限数で指定してください")
        else:
            values[key] = value

    mirrors = {}
    for key in ("mirror_x", "mirror_y"):
        value = snapshot.get(key, False)
        if type(value) is not bool:
            errors.append(f"{key}は真偽値で指定してください")
        else:
            mirrors[key] = value

    rotation = _finite_number(snapshot.get("rotation_degrees", 0))
    if rotation is None:
        errors.append("rotation_degreesは有限数で指定してください")

    plot_scale = _finite_number(snapshot.get("plot_scale", 1))
    if plot_scale not in (.5, .75, 1):
        errors.append("plot_scaleは0.5・0.75・1で指定してください")

    stage = snapshot.get("stage")
    dimensions = {}
    if not isinstance(stage, dict):
        errors.append("stageはx・y・width・heightを持つJSONオブジェクトで指定してください")
    else:
        for key in ("x", "y", "width", "height"):
            value = _finite_number(stage.get(key))
            if value is None or (key in {"width", "height"} and value <= 0):
                errors.append(f"stage.{key}は有限数で指定し、width・heightは正にしてください")
            else:
                dimensions[key] = value
    count = snapshot.get("count")
    if type(count) is not int or count < 2:
        errors.append("countは2以上の整数で指定してください")
    points = snapshot.get("points")
    if not isinstance(points, list) or not points:
        errors.append("pointsは1点以上の観測を持つ配列で指定してください")
    if errors:
        return _result(errors)

    scale = .44 * min(dimensions["width"], dimensions["height"]) * plot_scale
    origin_x = dimensions["x"] + dimensions["width"] / 2
    origin_y = dimensions["y"] + dimensions["height"] / 2
    phase = math.radians(values["phase_degrees"])
    clock = values["clock_radians"]
    amplitude = values["amplitude"]
    seen: set[int] = set()
    checked = 0
    maximum = 0.0
    for position, point in enumerate(points):
        prefix = f"points[{position}]"
        if not isinstance(point, dict):
            errors.append(f"{prefix}はindex・x・yを持つJSONオブジェクトで指定してください")
            continue
        index = point.get("index")
        if type(index) is not int or not 0 <= index < count:
            errors.append(f"{prefix}.indexは0〜{count - 1}の整数で指定してください")
            continue
        if index in seen:
            errors.append(f"{prefix}.indexが重複しています: {index}")
            continue
        seen.add(index)
        observed_x = _finite_number(point.get("x"))
        observed_y = _finite_number(point.get("y"))
        if observed_x is None or observed_y is None:
            errors.append(f"{prefix}のx・yは有限数で指定してください")
            continue
        u = index / (count - 1)
        theta = math.tau * u
        if model == "lissajous":
            x = amplitude * math.sin(values["k"] * theta + phase + clock)
            y = amplitude * math.sin(2 * theta + clock)
        elif model in {"wave", "damped-wave"}:
            x = 2 * u - 1
            envelope = math.exp(-3 * u) if model == "damped-wave" else 1
            y = amplitude * envelope * math.sin(values["k"] * theta + phase + clock)
        elif model == "standing-wave":
            x = 2 * u - 1
            y = amplitude * math.sin(values["k"] * theta + phase) * math.cos(clock)
        elif model == "rose":
            radius = amplitude * math.sin(values["k"] * theta + phase)
            x = radius * math.cos(theta + clock)
            y = radius * math.sin(theta + clock)
        elif model in {"spiral", "fermat"}:
            radius = amplitude * (math.sqrt(u) if model == "fermat" else u)
            angle = values["k"] * theta + phase + clock
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
        else:
            main = theta + clock
            secondary = values["k"] * theta + phase - clock
            x = amplitude * (.65 * math.cos(main) + .35 * math.cos(secondary))
            y = amplitude * (.65 * math.sin(main) - .35 * math.sin(secondary))
        x *= -1 if mirrors["mirror_x"] else 1
        y *= -1 if mirrors["mirror_y"] else 1
        angle = math.radians(rotation)
        x, y = x * math.cos(angle) - y * math.sin(angle), x * math.sin(angle) + y * math.cos(angle)
        expected_x = origin_x + scale * x
        expected_y = origin_y - scale * y
        if not math.isfinite(expected_x) or not math.isfinite(expected_y):
            errors.append(f"{prefix}の期待座標が有限数になりません")
            continue
        distance = math.hypot(observed_x - expected_x, observed_y - expected_y)
        checked += 1
        if not math.isfinite(distance):
            errors.append(f"{prefix}の座標差が有限数になりません")
            continue
        maximum = max(maximum, distance)
        if distance > limit:
            errors.append(
                f"{prefix}（index={index}）の誤差{distance:.9g} CSS pxが"
                f"許容差{limit:.9g} CSS pxを超えています"
            )
    return _result(errors, checked, maximum)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DOM観測JSONと独立した数式の座標照合")
    parser.add_argument("snapshot", nargs="?", type=Path)
    parser.add_argument("--batch", type=Path, help="同じディレクトリの観測JSONを列挙するmanifest")
    parser.add_argument("--tolerance", type=float, default=.1, help="許容差（CSS px、既定0.1）")
    args = parser.parse_args(argv)
    if (args.snapshot is None) == (args.batch is None):
        parser.error("単一snapshotか--batchの一方だけを指定してください")
    if args.batch is not None:
        from .coordinate_batch import inspect_batch
        result = inspect_batch(args.batch, args.tolerance)
    else:
        from .json_data import load_json
        try:
            data = load_json(args.snapshot)
        except (OSError, UnicodeError, ValueError) as error:
            result = _result([f"観測JSONを読み取れません: {error}"])
        else:
            result = inspect_snapshot(data, args.tolerance)
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
