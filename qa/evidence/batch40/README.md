# 追加20件のブラウザ証跡

2026-10-29、Chrome155、Linux User-Agent。条件と未検証範囲は[統合検証](../../../docs/batch40/validation.md)を参照する。

28個の座標JSONはtools.coordinatesの入力形式。DOMの点中心、stage矩形、観測した有効値・時計を記録した。各sampleのCSS変数--x/--yを期待値には使わない。results.jsonは全件の照合結果で、座標入力ではない。21ケース×192点とギャラリー7ケース×96点の合計4,704点。最大誤差0.000129933 CSS px、許容差0.1 CSS px。

```sh
python3 -m tools.coordinates qa/evidence/batch40/model-fermat.json
python3 -m tools.coordinates qa/evidence/batch40/fraction-damped-wave.json
python3 -m tools.coordinates qa/evidence/batch40/gallery-6.json
```

model-*.jsonは8モデル。fraction-*.jsonは新3モデルのk2.9。square/wideは領域比率、square-pointsは点形状。focus-before/on/afterは集中表示。preset-*.jsonは新3プリセット。gallery-1〜7.jsonは定義順の静止プレビュー各96点。print.jsonはCSSメディア分岐fixtureであり実際の紙面印刷ではない。

一部のケースは統合候補の先行コミットで取得した。その後の数式や座標変換は同じで、後続変更は設定見出し・説明文・CI・資料。最終候補で全JSONを再照合している。desktop.jpgは描画順の色と端点印を付けたk2.9のフェルマー渦巻き、gallery.jpgは比較一覧の先頭。どちらも実画面のJPEG。iframeの幅や文字サイズの検査を実機・実OSの結果には扱わない。
