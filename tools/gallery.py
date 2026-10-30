"""Static comparison page; reuse CSS model equations with source-defined values."""
from html import escape


def static_model_selectors(css, models):
    """Extend exact model-selection prefixes for static, radio-free miniatures."""
    for model in models:
        identifier = model['id']
        selector = f'.lab:has(#model-{identifier}:checked)'
        css = css.replace(selector, f'.lab:is(:has(#model-{identifier}:checked), [data-static-model="{identifier}"])')
    return css


def gallery_html(presets, models):
    names = {model['id']: model['name'] for model in models}
    definitions = {model['id']: model for model in models}
    rows = []
    for preset in presets:
        label = f"{names[preset['model']]}、反復{preset['k']}、位相{preset['phase']}度、振幅{preset['amplitude']}パーセント。時計0で停止。"
        samples = ''.join(f'<i class="sample" data-index="{index}" style="--index-fallback:{index};--count-fallback:96"></i>' for index in range(96))
        unavailable = (f'<p class="model-unavailable model-unavailable-{preset["model"]}">このブラウザでは、このモデルに必要なCSS数式の機能が不足しているため描画しません。</p>'
                       if definitions[preset['model']].get('capability') else '')
        rows.append(f'''<li data-gallery-model="{preset['model']}">
  <figure class="lab gallery-example" data-static-model="{preset['model']}" style="--k-raw:{preset['k']};--phase-raw:{preset['phase']};--amplitude-raw:{preset['amplitude']/100:g}">
    <div class="stage" role="img" aria-label="{escape(label, quote=True)}"><div class="axes" aria-hidden="true"></div><div class="plot" aria-hidden="true">{samples}</div></div>
    {unavailable}
    <figcaption class="gallery-unsupported">このブラウザではCSS描画に必要な機能が不足しています。名前と初期値は一覧の記載を確認してください。</figcaption>
  </figure>
  <section><h2><a href="{preset['file']}">{escape(preset['name'])}<span aria-hidden="true"> ↗</span></a></h2>
    <p>{escape(names[preset['model']])}</p>
    <dl><div><dt>反復 k</dt><dd>{preset['k']:.2f}</dd></div><div><dt>位相 φ</dt><dd>{preset['phase']}°</dd></div><div><dt>振幅 A</dt><dd>{preset['amplitude']}%</dd></div></dl>
    <p>96点・時計 t = 0・停止</p><a class="gallery-open" href="{preset['file']}">この形を開いて調整する</a>
  </section>
</li>''')
    filters = '<fieldset class="gallery-filter"><legend>モデルで絞る</legend><div class="view-choices"><label><input id="gallery-all" type="radio" name="gallery-model" checked><span>全件</span></label>' + ''.join(f'<label><input id="gallery-{m["id"]}" type="radio" name="gallery-model"><span>{escape(m["name"])}</span></label>' for m in models) + '</div></fieldset>'
    return '''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'none'; style-src 'self' 'unsafe-inline'; img-src 'none'; object-src 'none'; base-uri 'none'">
<title>形の一覧 — CSS 視覚シンセサイザー</title><link rel="stylesheet" href="style.css"><link rel="stylesheet" href="engine.css"></head>
<body class="gallery-page"><header class="page-header"><h1>CSS 視覚シンセサイザー</h1><a class="guide-link" href="index.html">標準の画面へ ↗</a></header>
<main class="gallery-main"><h1>形の一覧</h1><p class="gallery-intro">静止した初期状態を比較できます。図は96点、開いた画面は192点です。すべて時計 t = 0 で停止して始まります。縦横を同じ倍率で描いています。</p>
<p class="gallery-intro">別ページへ移動するため、現在の調整値や時間の保持は保証しません。操作状態を保存する一覧ではありません。</p>
''' + filters + '<fieldset class="gallery-layout"><legend>一覧の表示</legend><div class="view-choices"><label><input id="gallery-figures" type="radio" name="gallery-layout" checked><span>図と値</span></label><label><input id="gallery-values" type="radio" name="gallery-layout"><span>値だけ</span></label></div><p>図を隠しても点のHTMLは残ります。性能向上を保証する操作ではありません。</p></fieldset>' + '''<ol class="gallery-list">''' + '\n'.join(rows) + '''</ol></main><footer class="gallery-main"><span>HTML + CSS · 視覚の実験</span><a href="index.html">標準の画面へ戻る</a></footer></body></html>
'''
