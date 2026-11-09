"""Finite two-signal visual synthesizer; Python only generates static HTML/CSS."""
from html import escape

GROUPS = {'a': [('fa', 'A 周波数', [('1', '1 周期'), ('2', '2 周期'), ('3', '3 周期'), ('4', '4 周期'), ('6', '6 周期'), ('8', '8 周期')], '2', '--fa'), ], 'b': [], 'output': [], 'extra': []}
MODES = [('sum', '重ねる')]
TRANSPORT = ''
RESET = ''
HELP = '<p>波Aと波Bを重ねて、一つの形を作ります。</p>'


def control(key, title, choices, default, variable):
    options = ''.join(
        f'<option id="s-{key}-{i}" value="{escape(value)}"'
        f'{" selected" if value == default else ""}>{escape(label)}</option>'
        for i, (value, label) in enumerate(choices)
    )
    return f'<label class="s-control s-{key}">{escape(title)}<select name="{key}" aria-label="{escape(title)}">{options}</select></label>'


def bindings():
    return '\n'.join(
        f'.synth:has(#s-{key}-{i}:checked){{{variable}:{value};}}'
        for group in GROUPS.values() for key, _, choices, _, variable in group
        for i, (value, _) in enumerate(choices) if variable
    )


def synthesis_html():
    groups = ''
    for key, title, fallback in [('a', '波 A', 'サイン波 · 2周期'), ('b', '波 B', 'サイン波 · 3周期'), ('output', '合成', 'AとBを半分ずつ重ねる')]:
        fields = ''.join(control(*item) for item in GROUPS[key])
        if key == 'output' and len(MODES) > 1:
            fields = control('mode', '合成方法', MODES, 'sum', '') + fields
        groups += f'<fieldset class="s-group"><legend>{title}</legend>{fields or "<p>" + fallback + "</p>"}</fieldset>'
    extras = ''.join(control(*item) for item in GROUPS['extra'])
    if extras:
        groups += '<details class="s-extra"><summary>表示と動き</summary><div class="s-extra-fields">' + extras + '</div></details>'
    points = ''.join(f'<i class="sample s-dot" style="--i:{i}"></i>' for i in range(192))
    return f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="二つの波を作り、重ね、変調して絵にする。CSSだけで動く視覚シンセサイザー。">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'none'; style-src 'self' 'unsafe-inline'; img-src 'none'; object-src 'none'; base-uri 'none'">
<title>CSS Synthesizer — 波を合成して絵にする</title><link rel="stylesheet" href="style.css"><link rel="stylesheet" href="engine.css"></head>
<body class="s-body"><a class="skip-link" href="#s-controls">波を調整する</a>
<header class="s-header"><h1>CSS Synthesizer</h1><nav aria-label="画面の移動"><a href="#s-guide">遊び方</a><a href="gallery.html">曲線の資料</a></nav></header>
<main class="synth"><form id="s-form"><figure class="s-figure"><figcaption><h2>波を合成して、絵にする。</h2><p>AとBを変える → 合成する → 気に入ったところで止める</p></figcaption>
<div class="s-stage" role="img" aria-label="二つの波から作った合成結果。横軸は点の順番、縦軸は合成した値。"><div class="s-grid" aria-hidden="true"></div><div class="s-points" aria-hidden="true">{points}</div><span class="s-mark">A + B → OUT</span></div>
<p class="s-unsupported">この画面にはCSSの三角関数と:has()が必要です。対応する現行Chrome / Edgeで開いてください。</p>
<div class="s-transport">{TRANSPORT}{RESET}</div></figure>
<div class="s-controls" id="s-controls">{groups}</div></form>
<details class="s-guide" id="s-guide"><summary>何をすると、どう変わる？</summary>{HELP}</details>
<footer class="s-footer"><span>HTML + CSS · Visual synthesis</span><a href="samples-96.html">従来の曲線を調整</a><a href="https://github.com/furukawa1020/CSS-Synthesizer-">ソース</a></footer></main></body></html>'''
