"""DOMで観測した点の中心を、独立した数式でCSS px単位に照合する。"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys


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
    不正な入力はok:falseと日本語errorsを返す。
    """
    errors: list[str] = []
    limit = _finite_number(tolerance)
    if limit is None or limit < 0:
        errors.append("許容差は0以上の有限数で指定してください")
    if not isinstance(snapshot, dict):
        return _result(errors + ["snapshotはJSONオブジェクトで指定してください"])

    model = snapshot.get("model")
    if not isinstance(model, str) or model not in {"lissajous", "wave"}:
        errors.append("modelはlissajousまたはwaveで指定してください")
    values = {}
    for key, lower, upper in (
        ("k", 1, 8),
        ("phase_degrees", 0, 360),
        ("amplitude", .25, 1),
        ("clock_radians", 0, math.tau),
    ):
        value = _finite_number(snapshot.get(key))
        if value is None or not lower <= value <= upper:
            errors.append(f"{key}は{lower}〜{upper}の有限数で指定してください")
        else:
            values[key] = value

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

    scale = .44 * min(dimensions["width"], dimensions["height"])
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
        else:
            x = 2 * u - 1
            y = amplitude * math.sin(values["k"] * theta + phase + clock)
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
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--tolerance", type=float, default=.1, help="許容差（CSS px、既定0.1）")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.snapshot.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        result = _result([f"観測JSONを読み取れません: {error}"])
    else:
        result = inspect_snapshot(data, args.tolerance)
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
