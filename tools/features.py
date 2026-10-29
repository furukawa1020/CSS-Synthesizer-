"""A declarative syntax diagnostic; it does not run or certify browser behavior."""
from html import escape

# Each condition is a literal @supports condition used by the generated page.
FEATURES = (
    ('has', '入力と状態', ':has()', 'selector(:has(*))', '入力状態による選択', 'https://www.w3.org/TR/selectors-4/#relational'),
    ('scroll-timeline', '入力と状態', 'scroll-timeline', '(scroll-timeline: --probe inline)', '横スクロールをタイムラインにする', 'https://www.w3.org/TR/scroll-animations-1/'),
    ('animation-timeline', '入力と状態', 'animation-timeline', '(animation-timeline: --probe)', '入力値をスクロール位置から計算する', 'https://www.w3.org/TR/scroll-animations-1/'),
    ('timeline-scope', '入力と状態', 'timeline-scope', '(timeline-scope: --probe)', '入力帯と描画でタイムラインを共有する', 'https://www.w3.org/TR/scroll-animations-1/'),
    ('initial-target', '入力と状態', 'scroll-initial-target', '(scroll-initial-target: nearest)', 'プリセットの初期目盛りへ移動する', 'https://drafts.csswg.org/css-overflow-5/#scroll-initial-target'),
    ('scroll-button', '入力と状態', '::scroll-button()', 'selector(::scroll-button(inline-start))', '帯を大きく送るネイティブな矢印', 'https://drafts.csswg.org/css-overflow-5/#scroll-buttons'),
    ('scroll-snap', '入力と状態', 'scroll-snap-type', '(scroll-snap-type: inline mandatory)', '任意の目盛りへの吸着', 'https://www.w3.org/TR/css-scroll-snap-1/'),
    ('container', '座標と描画', 'size container / cqmin', '(container-type: size) and (width: 1cqmin)', '短辺を使い縦横を同じ倍率にする', 'https://www.w3.org/TR/css-contain-3/'),
    ('sin', '座標と描画', 'sin() / cos()', '(width: calc(sin(1rad) * 1px)) and (width: calc(cos(1rad) * 1px))', '各モデルの三角関数', 'https://www.w3.org/TR/css-values-4/#trig-funcs'),
    ('sqrt', '座標と描画', 'sqrt()', '(width: calc(sqrt(.25) * 1px))', 'フェルマー渦巻きの半径', 'https://www.w3.org/TR/css-values-4/#exponent-funcs'),
    ('exp', '座標と描画', 'exp()', '(width: calc(exp(0) * 1px))', '減衰波の包絡', 'https://www.w3.org/TR/css-values-4/#exponent-funcs'),
    ('atan2', '座標と描画', 'atan2()', '(rotate: atan2(1, 1))', '接線のベクトルから角度を求める', 'https://www.w3.org/TR/css-values-4/#trig-funcs'),
    ('siblings', '座標と描画', 'sibling-index() / sibling-count()', '(z-index: sibling-index()) and (z-index: sibling-count())', '点の順番と点数。未対応時は生成済みの値を使う', 'https://drafts.csswg.org/css-values-5/#tree-counting'),
    ('round', '数値の表示', 'round() / mod() / counter', '(opacity: round(nearest, .5, .1)) and (counter-reset: probe round(down, 1.5, 1) remainder mod(3, 2))', '有効値の丸めと整数部・小数部の表示', 'https://www.w3.org/TR/css-values-4/#round-func'),
    ('popover', '説明の表示', ':popover-open', 'selector(:popover-open)', 'Popoverの開状態のスタイル。開閉操作は別途確認する', 'https://html.spec.whatwg.org/multipage/popover.html'),
    ('modal', '説明の表示', ':modal', 'selector(:modal)', 'Dialogのモーダル状態のスタイル。Invoker Commandsの検出ではない', 'https://www.w3.org/TR/selectors-4/#modal-state'),
    ('anchor', '説明の表示', 'position-anchor / position-area', '(position-anchor: --probe) and (position-area: bottom)', '説明を操作元の近くへ置く', 'https://www.w3.org/TR/css-anchor-position-1/'),
    ('discrete', '説明の表示', 'transition-behavior / overlay', '(transition-behavior: allow-discrete) and (overlay: auto)', '開閉トランジション。@starting-styleの検出ではない', 'https://www.w3.org/TR/css-transitions-2/'),
)


def features_html():
    rows = []
    rules = []
    for identifier, category, name, condition, purpose, reference in FEATURES:
        rows.append(f'''<tr id="feature-{identifier}"><th scope="row"><code>{escape(name)}</code></th><td>{category}</td>
<td class="feature-state"><span class="feature-no">構文未対応</span><span class="feature-yes">構文対応</span></td>
<td>{purpose}</td><td><a href="{reference}">仕様</a></td></tr>''')
        rules.append(f'@supports {condition} {{ #feature-{identifier} .feature-no {{ display:none; }} #feature-{identifier} .feature-yes {{ display:inline; }} }}')
    return '''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'none'; style-src 'self' 'unsafe-inline'; img-src 'none'; object-src 'none'; base-uri 'none'">
<title>CSS機能の構文診断 — CSS 視覚シンセサイザー</title><link rel="stylesheet" href="style.css"><style>''' + '\n'.join(rules) + '''</style></head>
<body class="features-page"><header class="page-header"><h1>CSS 視覚シンセサイザー</h1><a class="guide-link" href="index.html">描画画面へ</a></header>
<main class="features-main"><h1>CSS機能の構文診断</h1>
<p>このページの「構文対応」は、ブラウザが実際の<code>@supports</code>条件を受理した結果です。JavaScriptは使いません。</p>
<p>構文を受理することと、入力・描画・フォーカス・性能が正しく動くことは別です。この表だけで動作を保証しません。「構文未対応」でも代替表示がある機能があります。組み合わせで必要な条件は描画画面の案内も確認してください。</p>
<div class="feature-table-wrap" tabindex="0" role="region" aria-label="CSS構文対応の表。必要に応じて横スクロールできます。"><table class="feature-table"><caption>入力・描画・表示で使うCSS構文</caption><thead><tr><th scope="col">機能</th><th scope="col">分類</th><th scope="col">このブラウザ</th><th scope="col">用途と範囲</th><th scope="col">参照</th></tr></thead><tbody>''' + '\n'.join(rows) + '''</tbody></table></div>
<section class="feature-manual"><h2>実際に動かして確認すること</h2>
<dl><div><dt>@propertyの登録とアニメーション</dt><dd>要手動確認。カスタムプロパティ宣言への@supportsは、登録・型・継承・補間の検出にはなりません。描画画面で停止・調整・再生を確認します。</dd></div>
<div><dt>Invoker Commands、Dialog、Popover</dt><dd>要手動確認。:modalや:popover-openの構文対応はcommandforの実動作の証拠ではありません。操作ガイドの開閉、Escape、フォーカス復帰を確認します。</dd></div>
<div><dt>@starting-style</dt><dd>要手動確認。transition-behaviorの行だけでこのat-ruleの対応を判定しません。動きを減らす設定も含めて開閉を確認します。</dd></div>
<div><dt>@counter-styleの桁埋め</dt><dd>要手動確認。3桁に埋める表示例：<output class="feature-pad" aria-label="カウンターの3桁表示例"></output>。000ならこの例のpad指定が反映されています。位相の換算値の正しさは別途照合します。</dd></div>
<div><dt>MathML</dt><dd>要手動確認。平方根の例<math xmlns="http://www.w3.org/1998/Math/MathML"><msqrt><mn>4</mn></msqrt><mo>=</mo><mn>2</mn></math>を表示します。数式の配置と読み上げは別々に確認します。</dd></div>
<div><dt>入力・読み上げ・性能</dt><dd>要手動確認。タッチ、キーボード、値の読み上げ、実OS設定、実端末での描画性能は構文の表では測れません。</dd></div></dl>
<p><a href="index.html">描画画面で操作する</a> · <a href="https://github.com/furukawa1020/CSS-Synthesizer-/issues/3">残る実機検証</a></p></section>
</main><footer class="features-main"><span>HTML + CSS · 構文診断</span><a href="index.html">描画画面へ戻る</a></footer></body></html>
'''
