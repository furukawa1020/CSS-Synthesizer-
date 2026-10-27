# HTML-in-Canvasの採用調査

Issue #12。調査日：2026-10-27（日本時間）。これは技術調査と実装計画であり、APIを実装・実測済みという記録ではない。

## 目的と現在の判断

ユーザーの指定は、会話内のHTMLプレビューではなく、HTML/CSSで作るDOMをCanvasへ描くHTML-in-Canvas APIの採用である。

一方、U-06は開発用も含めたJavaScriptゼロを指定している。現行APIでは、属性を付けるだけでCanvasに描画されない。実際の描画にJavaScriptのAPI呼び出しが必要なため、両要件を同時に満たす実装経路は確認できない。JS例外の扱いは未確定。現在の本体・開発ツール・配布物ではJSゼロを維持し、採用実装はIssue #12の未完了項目に残す。

## 現行API

| 要素 | 役割 | 本プロジェクトへの意味 |
| --- | --- | --- |
| `canvas content="drawable"` | Canvas子孫をレイアウトする | 属性だけではCanvasの画素を描かない |
| 子孫の`drawable`属性 | 独立した描画対象を指定する | 192点を包む描画領域を一つの対象にできる |
| `paint`イベント | DOMの描画内容の更新に同期する | CSSアニメーションや入力変更に伴う再描画を受け取る |
| 2Dの`drawElementImage()` | DOMの描画内容をCanvasへ転写する | JSから実行する。現在は返り値がvoid |
| `updateElementGeometry()` | 描いた場所と操作・アクセシビリティの座標を同期する | 現行2Dでは描画時に自動同期。3Dでは明示的な同期が必要 |

根拠：[WICG explainer][1]、[Chrome公式2D手順][2]。`content="drawable"`の子孫は、初期状態では操作用のgeometryが設定されていない。属性の追加のみで操作可能なCanvasとして扱わない。

## 旧記事との違いと提供状況

[Chrome公式の更新記事][3]では、Chrome 155以降で`layoutsubtree`を`content="drawable"`へ変更し、子孫に`drawable`を明示する。2Dの描画結果をDOMMatrixとして受け取り、CSS transformへ代入する旧パターンも採用しない。WebGLは`texElementSubImage2D`、WebGPUは`drawElementImageToTexture`が現行の名称。

同記事はOrigin TrialをChrome 160までとしている。調査時点の[WHATWG仕様PR][4]はOpen。安定した全ブラウザ対応機能として扱わない。WICGにはChromiumの`canvas-draw-element`フラグによる試用手順がある。今回このフラグの変更やAPI描画の実測は行っていない。

## JS例外を設ける場合の最小スパイク案

以下は提案であり、実装済み・例外確定ではない。

1. 別の実験ページで2D描画のみを検証する。既存本体と配布ZIPの監査は緩めない。
2. 数式、192点DOM、スクロール入力、停止・再開は既存CSSを使う。JSの責務はAPI検出、描画領域のサイズ・DPR対応、`paint`での転写、失敗時のDOM表示復帰に限定する。
3. APIの存在だけで成功にしない。初回の実描画を確認するまで元のDOMを利用可能に保ち、非対応・例外時にも作品と操作を失わない構成を検証する。
4. 旧APIへの互換コード、WebGL/WebGPU、worker、外部ライブラリ、書き出しは最初のスパイクに含めない。

この構成でもJSゼロではない。監査・CSP・README・要件の例外範囲を明示する必要がある。本体への採用判断は、実験結果の後に行う。

## 実測する項目

- 正確なブラウザ・OS・DPR・フラグまたは試験提供の状態、API存在。
- 初回描画とCSSアニメーション中の再描画。停止中の入力変更と再開。
- 通常DOMとCanvasの同一入力・時刻における描画比較。Canvas化だけで高速化したと主張しない。
- リサイズ、縦横比、DPR変更時の描画サイズと等倍率。
- ポインタ・Tab・キーボード・読み上げでのgeometry同期。
- API不在、描画例外、JS無効時に元のDOMが使えること。

CSSの`@supports`だけではCanvasのJS APIの存在・描画成功を検出できない。上記はすべて未実測であり、既存のCSS本体の検証結果を転用しない。

[1]: https://wicg.github.io/html-in-canvas/
[2]: https://developer.chrome.com/docs/web-platform/html-in-canvas/2d
[3]: https://developer.chrome.com/blog/html-in-canvas-ot-changes
[4]: https://github.com/whatwg/html/pull/11588
