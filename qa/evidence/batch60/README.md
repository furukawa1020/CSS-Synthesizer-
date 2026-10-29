# 比較と操作を拡張する20件の証跡

2026-10-30、Chrome155、Linux UA。[統合検証](../../../docs/batch60/validation.md)に条件と限界を記録する。

index.jsonは座標snapshot30件の明示一覧。合計4,513点で最大誤差0.011094050 CSS px、許容差0.1 CSS px。tangent-*.jsonは別形式の9ケース・1,633方向で、最大誤差0.000499943°、許容差0.1°。results.jsonは集計、layout.jsonはUI・構文・幅のメタデータであり、座標snapshotではない。

```sh
python3 -m tools.coordinates --batch qa/evidence/batch60/index.json
python3 -m tools.tangents qa/evidence/batch60/tangent-fermat.json
python3 -m tools.tangents qa/evidence/batch60/tangent-stationary-97.json
```

座標はDOMのsample中心とstage矩形、入力の有効値・時計から記録。接線は塗りの疑似要素のcomputed rotate（ローカル角）とopacity。CSSの座標変数・微分変数を期待値には使わない。全sampleを記録した。stationary-97はk2・φt0、97点で4箇所の微分ゼロを含めたfixture。比較印刷もCSSメディア分岐fixtureで、実際の印刷ではない。

compare.jpgは各192点の比較画面の実JPEG。観測の一部は先行候補で取得したが、その後の数式・表示変換・微分の式は同じ。最後に全JSONを独立照合した。狭い幅の角度凡例、ラジアン機能検出等の修正は最終候補で確認した。

QAページは正常なbuildの後、python3 -m tools.fixturesで生成できる。配布前にtools.build／tools.packageを実行すると検証用ページを除いた成果物へ置き換わる。iframe幅・文字拡大・CSS分岐を実機・OS・他ブラウザの合格と扱わない。
