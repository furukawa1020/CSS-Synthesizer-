"""Static comparison page; reuse CSS model equations with source-defined values."""
from html import escape
from .models import model_equations_html


def static_model_selectors(css, models):
    """Extend exact model-selection prefixes for static, radio-free miniatures."""
    for model in models:
        identifier = model['id']
        selector = f'.lab:has(#model-{identifier}:checked)'
        css = css.replace(selector, f'.lab:is(:has(#model-{identifier}:checked), [data-static-model="{identifier}"])')
    return css


GALLERY_COUNTS = (96, 192)


def gallery_filename(count):
    if type(count) is not int or count not in GALLERY_COUNTS:
        raise ValueError('一覧の点数は96または192で指定してください')
    return 'gallery.html' if count == 96 else f'gallery-{count}.html'


def gallery_html(presets, models, count=96):
    gallery_filename(count)
    names = {model['id']: model['name'] for model in models}
    definitions = {model['id']: model for model in models}
    rows = []
    for preset in presets:
        label = f"{names[preset['model']]}、反復{preset['k']}、位相{preset['phase']}度、振幅{preset['amplitude']}パーセント。時計0で停止。"
        samples = ''.join(f'<i class="sample" data-index="{index}" style="--index-fallback:{index};--count-fallback:{count}"></i>' for index in range(count))
        unavailable = (f'<p class="model-unavailable model-unavailable-{preset["model"]}">このブラウザでは、このモデルに必要なCSS数式の機能が不足しているため描画しません。</p>'
                       if definitions[preset['model']].get('capability') else '')
        rows.append(f'''<li id="gallery-item-{preset['file'].removesuffix('.html')}" tabindex="-1" data-gallery-model="{preset['model']}">
  <figure class="lab gallery-example" data-static-model="{preset['model']}" style="--k-raw:{preset['k']};--phase-raw:{preset['phase']};--amplitude-raw:{preset['amplitude']/100:g}">
    <div class="stage" role="img" aria-label="{escape(label, quote=True)}"><div class="axes" aria-hidden="true"></div><div class="plot" aria-hidden="true">{samples}</div></div>
    {unavailable}
    <figcaption class="gallery-unsupported">このブラウザではCSS描画に必要な機能が不足しています。名前と初期値は一覧の記載を確認してください。</figcaption>
  </figure>
  <section><h2><a href="{preset['file']}">{escape(preset['name'])}<span aria-hidden="true"> ↗</span></a></h2>
    <p>{escape(names[preset['model']])}</p>
    <dl><div><dt>反復 k</dt><dd>{preset['k']:.2f}</dd></div><div><dt>位相 φ</dt><dd>{preset['phase']}°</dd></div><div><dt>振幅 A</dt><dd>{preset['amplitude']}%</dd></div></dl>
    <p>96点・時計 t = 0・停止</p><details class="curve-formula"><summary>この形の式</summary><div class="equations">{model_equations_html(definitions[preset['model']])}</div></details><a class="gallery-open" href="{preset['file']}">この形を開いて調整する</a><br><a class="gallery-back" href="#gallery-index">形の索引へ戻る</a>
  </section>
</li>''')
    index = '<nav class="gallery-index" id="gallery-index" aria-label="各形への移動"><p>形へ移動</p><ul>' + ''.join(f'<li data-index-model="{p["model"]}"><a href="#gallery-item-{p["file"].removesuffix(".html")}">{escape(p["name"])}</a></li>' for p in presets) + '</ul></nav>'
    totals = '<p class="gallery-count">表示する形：<span data-count-all>' + str(len(presets)) + '</span>' + ''.join(f'<span data-count-model="{m["id"]}">{sum(p["model"] == m["id"] for p in presets)}</span>' for m in models) + '件</p>'
    filters = '<fieldset class="gallery-filter"><legend>モデルで絞る</legend><div class="view-choices"><label><input id="gallery-all" type="radio" name="gallery-model" checked><span>全件</span></label>' + ''.join(f'<label><input id="gallery-{m["id"]}" type="radio" name="gallery-model"><span>{escape(m["name"])}</span></label>' for m in models) + '</div></fieldset>'
    result = '''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'none'; style-src 'self' 'unsafe-inline'; img-src 'none'; object-src 'none'; base-uri 'none'">
<title>形の一覧 — CSS 視覚シンセサイザー</title><link rel="stylesheet" href="style.css"><link rel="stylesheet" href="engine.css"></head>
<body class="gallery-page"><a class="skip-link" href="#gallery-index">形の索引へ進む</a><header class="page-header"><h1>CSS 視覚シンセサイザー</h1><a class="guide-link" href="index.html">標準の画面へ ↗</a></header>
<main class="gallery-main"><h1>形の一覧</h1><p class="gallery-intro">静止した初期状態を比較できます。図は96点、開いた画面は192点です。すべて時計 t = 0 で停止して始まります。縦横を同じ倍率で描いています。</p>
<p class="gallery-intro">別ページへ移動するため、現在の調整値や時間の保持は保証しません。操作状態を保存する一覧ではありません。</p>
''' + filters + totals + '<fieldset class="gallery-layout"><legend>一覧の表示</legend><div class="view-choices"><label><input id="gallery-figures" type="radio" name="gallery-layout" checked><span>図と値</span></label><label><input id="gallery-values" type="radio" name="gallery-layout"><span>値だけ</span></label></div><p>図を隠しても点のHTMLは残ります。性能向上を保証する操作ではありません。</p></fieldset>' + '''<ol class="gallery-list">''' + '\n'.join(rows) + '''</ol></main><footer class="gallery-main"><span>HTML + CSS · 視覚の実験</span><a href="index.html">標準の画面へ戻る</a></footer></body></html>
'''
    result = result.replace('図は96点', f'図は{count}点').replace('<p>96点・', f'<p>{count}点・')
    navigation = '<nav class="gallery-density" aria-label="一覧の図ごとの点数">各図の点数 ' + ' / '.join(f'<strong aria-current="page">{n}点</strong>' if n == count else f'<a href="{gallery_filename(n)}">{n}点</a>' for n in GALLERY_COUNTS) + '</nav>'
    return result.replace('<ol class="gallery-list">', navigation + index + '<ol class="gallery-list">')


def gallery_styles(models):
    """Generate filter bindings from the same IDs that produce radio choices."""
    return '@supports selector(:has(*)) {\n' + '\n'.join(
        f'.gallery-main:has(#gallery-{m["id"]}:checked) .gallery-list > li:not([data-gallery-model="{m["id"]}"]) {{ display:none; }} .gallery-main:has(#gallery-{m["id"]}:checked) .gallery-index li:not([data-index-model="{m["id"]}"]) {{ display:none; }}'
        for m in models) + '\n' + '\n'.join(f'.gallery-main:has(#gallery-{m["id"]}:checked) .gallery-count [data-count-all] {{ display:none; }} .gallery-main:has(#gallery-{m["id"]}:checked) .gallery-count [data-count-model="{m["id"]}"] {{ display:inline; }}' for m in models) + '\n}' 
