"""Generate model descriptions from data; runtime equations stay in CSS."""
from html import escape
import json
from pathlib import Path
import re

TEXT_FIELDS = ('name', 'k_label', 'k_help', 'phase_help', 'amplitude_label', 'amplitude_help', 'note')
MATH_TOKEN = re.compile(r'sin|cos|\d+(?:\.\d+)?|[A-Za-z\u0370-\u03ff]|[=+−*/()\-]')


def mathml_expression(expression):
    """Render the project's deliberately small equation vocabulary as MathML."""
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError('数式は空でない文字列にしてください')
    compact = re.sub(r'\s+', '', expression)
    tokens = MATH_TOKEN.findall(compact)
    if ''.join(tokens) != compact:
        raise ValueError('数式に未対応の記号が含まれています')
    nesting = 0
    output = []
    for token in tokens:
        if token == '(':
            nesting += 1
        elif token == ')':
            nesting -= 1
            if nesting < 0:
                raise ValueError('数式の括弧が対応していません')
        if token in {'sin', 'cos'}:
            output.append(f'<mi mathvariant="normal">{token}</mi><mo>⁡</mo>')
        elif token[0].isdigit():
            output.append(f'<mn>{token}</mn>')
        elif token.isalpha():
            output.append(f'<mi>{escape(token)}</mi>')
        else:
            operator = {'-': '−', '*': '×'}.get(token, token)
            output.append(f'<mo>{escape(operator)}</mo>')
    if nesting:
        raise ValueError('数式の括弧が対応していません')
    return '<math xmlns="http://www.w3.org/1998/Math/MathML" display="block"><mrow>' + ''.join(output) + '</mrow></math>'


def validate_models(models):
    if not isinstance(models, list) or not models:
        raise ValueError('モデル定義は空でない配列にしてください')
    seen = set()
    for model in models:
        if not isinstance(model, dict):
            raise ValueError('モデル定義はオブジェクトにしてください')
        identifier = model.get('id')
        if not isinstance(identifier, str) or not re.fullmatch(r'[a-z][a-z0-9-]*', identifier) or identifier in seen:
            raise ValueError('モデルIDが不正または重複しています')
        seen.add(identifier)
        if any(not isinstance(model.get(key), str) or not model[key].strip() for key in TEXT_FIELDS):
            raise ValueError(f'{identifier}の表示説明が不足しています')
        equations = model.get('equations')
        if not isinstance(equations, list) or len(equations) != 2 or any(not isinstance(value, str) or not value.strip() for value in equations):
            raise ValueError(f'{identifier}にはx・yの2式が必要です')
    return models


def load_models(source):
    return validate_models(json.loads((Path(source) / 'models.json').read_text(encoding='utf-8')))


def model_tokens(models, selected='lissajous'):
    validate_models(models)
    if selected not in {model['id'] for model in models}:
        raise ValueError('既定のモデルが定義されていません')
    def copies(key):
        return ''.join(f'<span class="for-{m["id"]}" data-model-copy="{m["id"]}">{escape(m[key])}</span>' for m in models)
    result = {
        '@@MODEL_CHOICES@@': ''.join(
            f'<label><input id="model-{m["id"]}" type="radio" name="model" value="{m["id"]}"'
            f'{" checked" if m["id"] == selected else ""}><span>{escape(m["name"])}</span></label>' for m in models),
        '@@MODEL_NAMES@@': copies('name'),
        '@@MODEL_K_LABELS@@': copies('k_label'),
        '@@MODEL_K_HELP@@': copies('k_help'),
        '@@MODEL_PHASE_HELP@@': copies('phase_help'),
        '@@MODEL_AMPLITUDE_LABELS@@': copies('amplitude_label'),
        '@@MODEL_AMPLITUDE_HELP@@': copies('amplitude_help'),
        '@@MODEL_NOTES@@': copies('note'),
        '@@MODEL_EQUATIONS@@': ''.join(
            f'<div class="for-{m["id"]}" data-model-copy="{m["id"]}" style="--model-copy-display:block">'
            + ''.join(mathml_expression(part.strip()) for value in m['equations'] for part in value.split(';'))
            + '</div>' for m in models),
    }
    return result


def model_styles(models):
    validate_models(models)
    return '[data-model-copy] { display: none; }\n' + '\n'.join(
        f'.lab:has(#model-{m["id"]}:checked) [data-model-copy="{m["id"]}"] '
        '{ display: var(--model-copy-display, inline); }' for m in models)
