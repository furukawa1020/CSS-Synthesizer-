"""Compile explicit JSON starting states; no browser state is read or saved."""
from pathlib import Path
from decimal import Decimal
import math
from .build import ROOT
from .json_data import loads_json
from .models import load_models

MAX_SCENE_BYTES = 16 * 1024
FIELDS = {'version', 'model', 'k', 'phase', 'amplitude', 'count', 'clock_radians', 'view', 'processing', 'title', 'clock_period_seconds', 'clock_direction'}


def validate_scene(data, source=ROOT / 'src'):
    if not isinstance(data, dict) or set(data) - FIELDS:
        raise ValueError('sceneは許可されたキーだけのJSONオブジェクトにしてください')
    if type(data.get('version')) is not int or data['version'] != 1:
        raise ValueError('sceneのversionは1です')
    model = data.get('model')
    if not isinstance(model, str) or model not in {m['id'] for m in load_models(source)}:
        raise ValueError('sceneのmodelが未対応です')
    result = dict(version=1, model=model, k=data.get('k', 3), phase=data.get('phase', 90),
                  amplitude=data.get('amplitude', 80), count=data.get('count', 192))
    if type(result['count']) is not int or result['count'] not in (96, 192, 384):
        raise ValueError('countは96/192/384です')
    for key, low, high, scale in (('k', 1, 8, 100), ('phase', 0, 360, 1), ('amplitude', 25, 100, 1)):
        value = result[key]
        if (type(value) not in (int, float) or not low <= value <= high or not math.isfinite(value)
                or Decimal(str(value)) * scale != (Decimal(str(value)) * scale).to_integral_value()):
            raise ValueError(f'{key}は範囲内の対応する精度で指定してください')
        result[key] = float(value) if key == 'k' else int(value)
    clock = data.get('clock_radians', 0)
    if type(clock) not in (int, float) or not 0 <= clock <= math.tau or not math.isfinite(clock):
        raise ValueError('clock_radiansは0〜2πの有限数です')
    result['clock_radians'] = float(clock)
    result['view'] = validate_view(data.get('view', {}), source)
    from .processing import processing_options
    processing, errors = processing_options(data.get('processing', {}))
    if errors:
        raise ValueError('; '.join(errors))
    result['processing'] = processing
    title = data.get('title', '保存シーン')
    if not isinstance(title, str) or not title.strip() or len(title) > 120 or any(ord(c) < 32 or 127 <= ord(c) < 160 for c in title):
        raise ValueError('titleは1〜120文字の1行テキストです')
    result['title'] = title.strip()
    period = data.get('clock_period_seconds', 24)
    direction = data.get('clock_direction', 'forward')
    if type(period) is not int or period not in (6, 12, 24, 48, 96):
        raise ValueError('clock_period_secondsは6/12/24/48/96です')
    if not isinstance(direction, str) or direction not in ('forward', 'reverse'):
        raise ValueError('clock_directionはforward/reverseです')
    result['clock_period_seconds'] = period
    result['clock_direction'] = direction
    return result


def load_scene(path, source=ROOT / 'src'):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('sceneは通常のJSONファイルにしてください')
    with path.open('rb') as stream:
        raw = stream.read(MAX_SCENE_BYTES + 1)
    if len(raw) > MAX_SCENE_BYTES:
        raise ValueError('sceneは16KiB以下にしてください')
    try:
        data = loads_json(raw.decode('utf-8'))
    except RecursionError as error:
        raise ValueError('sceneのJSONが深すぎます') from error
    return validate_scene(data, source)


def render_scene(data, source=ROOT / 'src'):
    from .build import single_html
    from .source import expand_fragments
    from .presets import load_presets
    scene = validate_scene(data, source)
    models = load_models(source)
    presets = load_presets(source, {m['id'] for m in models})
    template = expand_fragments((Path(source) / 'page.html').read_text(encoding='utf-8'), source)
    state = dict(scene, name='保存シーン', file='index.html')
    html = single_html(template, models, presets, scene['count'], state)
    # Additional initial targets use the existing continuous track; they do not
    # insert an extra interval or change the standard jump link IDs.
    for prefix, value, low, step, text in (
        ('k', scene['k'], 1, 1, f"{scene['k']:.2f}"),
        ('phase', scene['phase'], 0, 90, f"{scene['phase']}°"),
        ('amplitude', scene['amplitude'], 25, 5, f"{scene['amplitude']}%"),
    ):
        if (value - low) % step:
            import re
            track = re.compile(r'(<div class="input-band input-' + prefix + r'"[^>]*><div class="ticks"[^>]*>)(.*?)(</div>)', re.S)
            def add(match):
                content = match[2].replace('tick initial', 'tick')
                target = f'<span class="tick initial scene-initial" style="--tick-index:{(value-low)/step:g}">{text}</span>'
                return match[1] + content + target + match[3]
            html, changed = track.subn(add, html)
            if changed != 1:
                raise ValueError('保存シーンの初期位置を設定できません')
    html = html.replace('<main class="lab" style="', f'<main class="lab" style="--clock-start:{scene["clock_radians"]:.17g};', 1)
    html = apply_controls(html, {'clock-period':f'period-{scene["clock_period_seconds"]}', 'clock-direction':f'direction-{scene["clock_direction"]}'})
    html = apply_controls(html, scene['view'])
    html = apply_controls(html, processing_controls(scene['processing']))
    from html import escape
    title = escape(scene['title'])
    html = html.replace('<title>CSS 視覚シンセサイザー</title>', f'<title>{title} — CSS 視覚シンセサイザー</title>')
    html = html.replace('<figure class="scene">', f'<figure class="scene"><h2 class="saved-scene-title">{title}</h2>', 1)
    html = html.replace('表示設定だけを標準へ戻す', '保存シーンの表示設定へ戻す')
    return html


def view_inputs(source=ROOT / 'src'):
    from html.parser import HTMLParser
    from .source import expand_fragments
    class Inputs(HTMLParser):
        def __init__(self): super().__init__(); self.inputs = {}
        def handle_starttag(self, tag, pairs):
            attrs = dict(pairs)
            if tag == 'input' and attrs.get('type') in ('radio', 'checkbox'):
                self.inputs[attrs['id']] = attrs
    parser = Inputs()
    path = Path(source) / 'fragments/view-settings.html'
    parser.feed(expand_fragments(path.read_text(encoding='utf-8'), source))
    return parser.inputs


def view_schema(source=ROOT / 'src'):
    """Expose the actual accepted keys, choices, and default selections."""
    result = {}
    for identifier, attrs in view_inputs(source).items():
        name = attrs.get('name', identifier)
        if name.startswith(('coordinate-', 'gain-', 'offset-')):
            continue
        if attrs['type'] == 'checkbox':
            result[identifier] = {'type': 'boolean', 'default': 'checked' in attrs}
        else:
            field = result.setdefault(name, {'type': 'choice', 'choices': [], 'default': None})
            field['choices'].append(identifier)
            if 'checked' in attrs:
                field['default'] = identifier
    return result


def validate_view(value, source=ROOT / 'src'):
    if not isinstance(value, dict):
        raise ValueError('viewはオブジェクトです')
    radios = {}
    checkboxes = set()
    for identifier, attrs in view_inputs(source).items():
        name = attrs.get('name', identifier)
        if name.startswith(('coordinate-', 'gain-', 'offset-')):
            continue
        if attrs['type'] == 'radio':
            radios.setdefault(name, set()).add(identifier)
        else:
            checkboxes.add(identifier)
    for key, item in value.items():
        if key in checkboxes and type(item) is bool:
            continue
        if key in radios and isinstance(item, str) and item in radios[key]:
            continue
        raise ValueError(f'view.{key}は対応する表示設定ではありません')
    return dict(value)


def apply_controls(html, selections):
    import re
    def choose(match):
        tag = match[0]
        attrs = dict(re.findall(r'([a-z-]+)="([^"]*)"', tag))
        identifier = attrs.get('id')
        key = attrs.get('name', identifier)
        if key not in selections:
            return tag
        value = selections[key]
        selected = value if type(value) is bool else value == identifier
        tag = re.sub(r'\schecked(?=[\s>])', '', tag)
        return tag[:-1] + (' checked>' if selected else '>')
    return re.sub(r'<input\b[^>]*>', choose, html)


def processing_controls(options):
    def gain(axis): return f'gain-{axis}-' + {.5:'half',1:'one',2:'two'}[options[f'gain_{axis}']]
    def offset(axis): return f'offset-{axis}-' + {-.25:'minus',0:'zero',.25:'plus'}[options[f'offset_{axis}']]
    return {
        'coordinate-swap':options['swap'], 'coordinate-fold':'fold-' + options['fold'],
        'coordinate-projection':'project-' + options['projection'],
        'gain-x':gain('x'), 'gain-y':gain('y'), 'offset-x':offset('x'), 'offset-y':offset('y'),
        'coordinate-quantize':'quant-' + {0:'none',.1:'tenth',.25:'quarter',.5:'half'}[options['quantum']],
        'coordinate-bound':options['bound'],
    }


def export_scene(data, destination, root=ROOT):
    """Install a new self-contained directory; never replace existing output."""
    import os
    import tempfile
    from .source import compose_css
    from .gallery import static_model_selectors
    from .models import model_styles
    from .comparison import comparison_styles
    from .gallery import gallery_styles
    from .model_engines import validate_engine_models
    from .audit import audit_directory
    root = Path(root)
    source = root / 'src'
    scene = validate_scene(data, source)
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError('出力先は存在しない新しいフォルダーにしてください')
    if not destination.parent.is_dir():
        raise ValueError('出力先の親ディレクトリがありません')
    models = load_models(source)
    specs = (('index.html', scene['count']), ('style.css', None), ('engine.css', None))
    with tempfile.TemporaryDirectory(prefix='.scene-candidate-', dir=destination.parent) as folder:
        candidate = Path(folder) / 'output'
        candidate.mkdir()
        html = standalone_html(render_scene(scene, source))
        (candidate / 'index.html').write_text(html, encoding='utf-8')
        for name in ('style.css', 'engine.css'):
            css = compose_css(source, name)
            if name == 'style.css':
                css += '\n' + gallery_styles(models) + '\n' + model_styles(models) + '\n' + comparison_styles(models)
            else:
                validate_engine_models(models, css)
            (candidate / name).write_text(static_model_selectors(css, models), encoding='utf-8')
        result = audit_directory(candidate, assets=specs)
        if not result['ok']:
            raise ValueError('; '.join(result['errors']))
        (candidate / 'scene.json').write_text(canonical_scene(scene, source), encoding='utf-8')
        # mkdir is exclusive, unlike rename over an empty directory. Move into
        # that reservation, removing only our own empty reservation on failure.
        destination.mkdir()
        try:
            for path in candidate.iterdir():
                os.replace(path, destination / path.name)
        except OSError:
            for name in (*[name for name, _ in specs], 'scene.json'):
                (destination / name).unlink(missing_ok=True)
            destination.rmdir()
            raise
    return destination


def standalone_html(html):
    import re
    html = re.sub(r'<section class="play-start"[^>]*>.*?</section>', '', html, flags=re.S)
    html = re.sub(r'<a class="choose-again"[^>]*>.*?</a>', '', html, flags=re.S)
    html = re.sub(r'<details class="preset-picker">.*?</details>', '', html, flags=re.S)
    html = re.sub(r'<nav class="density-picker"[^>]*>.*?</nav>', '', html, flags=re.S)
    html = re.sub(r'<p>描画点数：.*?</p>', '<p>点数は保存シーンJSONのcountで指定します。変更する場合は再生成してください。</p>', html, flags=re.S)
    def local_link(match):
        href = match[2]
        return match[0] if href.startswith(('#', 'https://')) else ''
    html = re.sub(r'<a\b([^>]*?)href="([^"]+)"([^>]*)>(.*?)</a>', local_link, html, flags=re.S)
    return html.replace('<div class="workspace">', '<p class="saved-scene-note">保存シーンの単独出力です。モデルと入力はこの画面で調整できます。別ページの一覧・点数切替は含みません。ブラウザー内の変更は自動保存されません。</p><div class="workspace">', 1)


def canonical_scene(data, source=ROOT / 'src'):
    import json
    return json.dumps(validate_scene(data, source), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n'


def main(argv=None):
    import argparse
    import sys
    parser = argparse.ArgumentParser(description='JSONの保存シーンからHTML/CSSを生成する')
    parser.add_argument('scene', nargs='?', type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--output', type=Path, help='新規出力フォルダー')
    mode.add_argument('--check', action='store_true', help='検査だけ行い、ファイルを生成しない')
    mode.add_argument('--canonical', action='store_true', help='正規化したJSONを標準出力へ出す')
    mode.add_argument('--list-view', action='store_true', help='viewのキーと選択IDをJSONで列挙')
    mode.add_argument('--list-models', action='store_true', help='利用できるモデルIDをJSONで列挙')
    parser.add_argument('--json', action='store_true', help='検査・出力の結果をJSONで返す')
    args = parser.parse_args(argv)
    import json
    def report(ok, **fields):
        print(json.dumps(dict(ok=ok, **fields), ensure_ascii=False))
    if args.json and (args.canonical or args.list_view or args.list_models):
        parser.error('--jsonは--checkまたは--outputと組み合わせます')
    if args.list_view or args.list_models:
        if args.scene is not None:
            parser.error('一覧取得にsceneは指定しません')
        import json
        print(json.dumps(view_schema() if args.list_view else [m['id'] for m in load_models(ROOT / 'src')], ensure_ascii=False, indent=2))
        return 0
    if args.scene is None:
        parser.error('sceneを指定してください')
    try:
        data = load_scene(args.scene)
        if args.canonical:
            print(canonical_scene(data), end='')
            return 0
        if args.check:
            if args.json: report(True, scene=data)
            else: print('保存シーンは有効です')
            return 0
        output = export_scene(data, args.output)
    except (OSError, ValueError, UnicodeError) as error:
        if args.json: report(False, errors=[str(error)])
        else: print(f'保存シーンを生成できません: {error}', file=sys.stderr)
        return 1
    if args.json: report(True, output=str(output), index=str(output / 'index.html'))
    else: print(f'保存シーンを生成しました: {output / "index.html"}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
