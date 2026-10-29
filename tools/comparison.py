"""Compare model equations with shared CSS input and clock values."""
from html import escape

COMPARISON_MODEL_IDS = ('lissajous', 'wave')


def comparison_models(models):
    return [model for model in models if model['id'] in COMPARISON_MODEL_IDS]


def comparison_html(template, parameters, models, count=96):
    """Reuse model-selection CSS through nested static-model scopes, not formulas."""
    selected = comparison_models(models)
    plots = []
    for model in selected:
        samples = ''.join(
            f'<i class="sample" data-index="{index}" style="--index-fallback:{index};--count-fallback:{count}"></i>'
            for index in range(count)
        )
        plots.append(f'''<figure class="lab comparison-example" data-static-model="{model['id']}">
  <div class="stage" role="img" aria-label="{escape(model['name'], quote=True)}の点の軌跡。共有入力と時計で描画。">
    <div class="stage-heading" aria-hidden="true"><span>{escape(model['name'])}</span><span>{count} 点</span></div>
    <div class="axes" aria-hidden="true"></div><div class="plot" aria-hidden="true">{samples}</div>
    <div class="stage-footnote" aria-hidden="true"><span>原点は中央</span><span>縦横等倍率</span></div>
  </div>
  <figcaption><h2>{escape(model['name'])}</h2><p>k：{escape(model['k_help'])}。A：{escape(model['amplitude_help'])}。</p><p>{escape(model['note'])}</p></figcaption>
</figure>''')
    generic = {
        '@@MODEL_K_LABELS@@': '反復 k', '@@MODEL_K_HELP@@': '各モデルの反復・巻き数を同時に変える',
        '@@MODEL_PHASE_HELP@@': '各モデルの位相 φ を同時に変える',
        '@@MODEL_AMPLITUDE_LABELS@@': '振幅 A', '@@MODEL_AMPLITUDE_HELP@@': '各モデルの振幅を同時に変える',
    }
    for token, value in generic.items():
        parameters = parameters.replace(token, value)
    return template.replace('@@COMPARISON_PLOTS@@', '\n'.join(plots)).replace('@@COMPARISON_PARAMETERS@@', parameters)
