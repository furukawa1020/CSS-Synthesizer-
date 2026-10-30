"""Compare model equations with shared CSS input and clock values."""
from html import escape

DEFAULT_COMPARISON_MODELS = ('lissajous', 'wave')
COMPARISON_COUNTS = (96, 192)


def comparison_filename(count):
    if type(count) is not int or count not in COMPARISON_COUNTS:
        raise ValueError('比較図の点数は96または192で指定してください')
    return 'compare.html' if count == 96 else f'compare-{count}.html'


def comparison_models(models):
    return list(models)


def comparison_html(template, parameters, models, count=96):
    """Reuse model-selection CSS through nested static-model scopes, not formulas."""
    filename = comparison_filename(count)
    selected = comparison_models(models)
    plots = []
    options = []
    for model in selected:
        checked = ' checked' if model['id'] in DEFAULT_COMPARISON_MODELS else ''
        options.append(f'<label><input type="checkbox" id="compare-{model["id"]}"{checked}><span>{escape(model["name"])}</span></label>')
        samples = ''.join(
            f'<i class="sample" data-index="{index}" style="--index-fallback:{index};--count-fallback:{count}"></i>'
            for index in range(count)
        )
        unavailable = (f'<p class="model-unavailable model-unavailable-{model["id"]}">このモデルに必要なCSS数式の機能が不足しているため描画しません。</p>' if model.get('capability') else '')
        plots.append(f'''<figure class="lab comparison-example" data-static-model="{model['id']}">
  <div class="stage" role="img" aria-label="{escape(model['name'], quote=True)}の点の軌跡。共有入力と時計で描画。">
    <div class="stage-heading" aria-hidden="true"><span>{escape(model['name'])}</span><span>{count} 点</span></div>
    <div class="axes" aria-hidden="true">@@FRAGMENT:axis-labels@@</div><div class="plot" aria-hidden="true">{samples}</div>
    <div class="stage-footnote" aria-hidden="true"><span>原点は中央</span><span>縦横等倍率</span></div>
  </div>
  {unavailable}
  <figcaption>@@FRAGMENT:polar-legend@@@@FRAGMENT:order-legend@@<h2>{escape(model['name'])}</h2><p>k：{escape(model['k_help'])}。φ：{escape(model['phase_help'])}。A：{escape(model['amplitude_help'])}。</p><p>{escape(model['note'])}</p></figcaption>
</figure>''')
    generic = {
        '@@MODEL_K_LABELS@@': '反復 k', '@@MODEL_K_HELP@@': '各モデルの反復・巻き数を同時に変える',
        '@@MODEL_PHASE_HELP@@': '各モデルの位相 φ を同時に変える',
        '@@MODEL_AMPLITUDE_LABELS@@': '振幅 A', '@@MODEL_AMPLITUDE_HELP@@': '各モデルの振幅を同時に変える',
    }
    for token, value in generic.items():
        parameters = parameters.replace(token, value)
    densities = ' / '.join(f'<strong aria-current="page">{n}点</strong>' if n == count else f'<a href="{comparison_filename(n)}">{n}点</a>' for n in COMPARISON_COUNTS)
    return template.replace('@@COMPARISON_COUNT@@', str(count)).replace('@@COMPARISON_DENSITIES@@', densities).replace('@@COMPARISON_PLOTS@@', '\n'.join(plots)).replace('@@COMPARISON_PARAMETERS@@', parameters).replace('@@COMPARISON_OPTIONS@@', '\n'.join(options))


def comparison_styles(models):
    rules = ['@supports selector(:has(*)) {',
             '.comparison-selection { display: block; }',
             '.comparison-example.lab { display: none; }',
             '.comparison-empty { display: block; }',
             '.comparison-lab:has(.comparison-selection input:checked) .comparison-empty { display: none; }']
    for model in models:
        identifier = model['id']
        rules.append(f'.comparison-lab:has(#compare-{identifier}:checked) .comparison-example[data-static-model="{identifier}"] {{ display: block; }}')
    rules.append('}')
    from .models import CAPABILITIES
    for model in models:
        if model.get('capability'):
            condition = CAPABILITIES[model['capability']][0]
            rules.append(f'@supports not ({condition}) {{ .comparison-selection label:has(#compare-{model["id"]}) {{ display: none; }} }}')
    return '\n'.join(rules)
