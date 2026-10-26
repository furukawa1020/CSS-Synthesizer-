# Issue #6：機能検出と静的監査の補強

検証日：2026-10-27（日本時間）。対象は連続入力に使うCSS宣言の検出と、配布物の静的ガード。見た目、数式、パラメータ範囲は変更しない。

## 修正前に確認したこと

連続入力は名前付きのscroll timelineを使うが、機能検出は匿名の`animation-timeline: scroll()`を検査していた。また、モデル・時間状態を切り替える`:has()`と、座標系を定義する`container-type: size`が条件に入っていなかった。

静的監査では、次のどちらも`ok: true`になることをNodeで実行確認した。

```html
<iframe src="data:text/html,test"></iframe>
<object data="data:text/html,test"></object>
```

配布ページのCSPとは別に、HTML/CSSだけの成果物というプロジェクト方針を静的監査でも守る必要がある。

## 変更

連続入力の検出条件を実際に使用する名前付きtimeline、リスト形式のscope、初期スクロール位置、size container、cqmin、丸めと剰余、三角関数、`:has()`、マウス操作に使う`::scroll-button()`に合わせた。

```css
@supports (scroll-timeline: --k-input inline)
  and (animation-timeline: --k-input)
  and (timeline-scope: --k-input, --phase-input, --amplitude-input)
  and (scroll-initial-target: nearest)
  and (container-type: size)
  and (width: 1cqmin)
  and (opacity: round(nearest, .5, .1))
  and (counter-reset: probe round(down, 1.5, 1) remainder mod(3, 2))
  and (width: calc(sin(1rad) * 1px))
  and selector(:has(*))
  and selector(::scroll-button(inline-start)) {
  /* 連続入力を有効化する */
}
```

`sibling-index()`による最適化は、同時に使う`sibling-count()`にも対応している場合に限定した。未対応時は生成済みのインデックスを使う。

監査では`iframe`・`object`・`embed`を禁止要素に加えた。この作品では別文書の埋め込みを必要としないため、リモートURLだけを調べるのではなく要素自体を拒否する。data URL、ローカルURL、URLのない要素、大文字の要素名を使った回帰テストを追加した。

## 検証結果

```sh
python3 -m tools.build
python3 -m unittest discover -s tests -v
python3 -m tools.audit
git diff --check
```

- ビルド成功。3つのHTMLと2つのCSSを生成。
- Python版の監査13件と、座標・生成・配布を含む計24件のテストが成功。新規の回帰テストは上記の埋め込み経路を拒否する。
- 生成物3 HTML / 2 CSSの静的監査に合格。
- 空白差分チェックに合格。

監査はIssue #7でPythonへ移行済み。UI側に同じ条件を適用し、360px / 1280pxのCSS分岐fixtureで描画非対応時に操作が再表示されないことを確認した。Safari・Firefox・旧Chromeでの動作確認として扱わない。

## 機能検出の限界

`@supports`による宣言やselectorの検査は、構文と機能の対応を選別するものであり、スクロール入力・補間・描画の正しさを実行して証明するものではない。対応条件を満たしても、[Issue #3](https://github.com/furukawa1020/CSS-Synthesizer-/issues/3)の実ブラウザ検証は必要である。

`@supports (--clock: 1)`では、`@property`の登録や数値補間を検査できない。カスタムプロパティの宣言検査は、登録済みかどうかにかかわらず汎用の値構文で評価される。本実装ではこの検査を登録対応の証拠にせず、Issue #1で観察した数値補間・表示・座標の結果と区別する。`at-rule()`による検査の追加対応を新たな必須条件にすることも、この変更では行わない。

静的監査は管理された本プロジェクトの生成物用であり、任意のHTML/CSSを安全化するサニタイザーではない。CSPや実際の配布物の確認を代替しない。

## 根拠

- [MDN：@supports](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40supports)：宣言とselectorの機能検査。
- [MDN：scroll-timeline](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/scroll-timeline)：名前付きtimelineの宣言。
- [MDN：timeline-scope](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/timeline-scope)：名前付きtimelineのscopeを拡張する機能。
- [CSS Properties and Values API Level 1：Conditional Rules](https://drafts.css-houdini.org/css-properties-values-api/#conditional-rules)：カスタムプロパティを`@supports`で検査する際の登録状態の扱い。
