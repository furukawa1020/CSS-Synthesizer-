# 20件の追加実装

2026-10-28（日本時間）の実装バッチ。ユーザー指定のIssueベース・日本語PRによる進行と、開発用を含むJSゼロを維持する。画面は描画と3本の調整帯を主役にし、補助的な設定・説明を必要時に開く。

## 実装一覧

各記録には実装範囲と検査の限界を残す。作成・統合したPRは、対応するGitHub Issueから追跡できる。

| Issue | 実装 | 個別の記録 |
| --- | --- | --- |
| [#17](https://github.com/furukawa1020/CSS-Synthesizer-/issues/17) | HTML断片・CSS拡張を配布時に合成 | [生成の基盤](issue-17.md) |
| [#18](https://github.com/furukawa1020/CSS-Synthesizer-/issues/18) | モデルの名称・入力ラベル・式を共通定義から生成 | [モデル定義](issue-18.md) |
| [#19](https://github.com/furukawa1020/CSS-Synthesizer-/issues/19) | 花弁モデル | [花弁](issue-19.md) |
| [#20](https://github.com/furukawa1020/CSS-Synthesizer-/issues/20) | 渦巻きモデル | [渦巻き](issue-20.md) |
| [#21](https://github.com/furukawa1020/CSS-Synthesizer-/issues/21) | 主円と副円による合成軌道モデル | [合成軌道](issue-21.md) |
| [#22](https://github.com/furukawa1020/CSS-Synthesizer-/issues/22) | 表示設定のネイティブPopover | [表示設定](issue-22.md) |
| [#23](https://github.com/furukawa1020/CSS-Synthesizer-/issues/23) | 直交／極座標／なしの補助線 | [補助線](issue-23.md) |
| [#24](https://github.com/furukawa1020/CSS-Synthesizer-/issues/24) | 2／3／5pxの点の太さ | [点の太さ](issue-24.md) |
| [#25](https://github.com/furukawa1020/CSS-Synthesizer-/issues/25) | 温色・青白・紙面の描画配色 | [配色](issue-25.md) |
| [#26](https://github.com/furukawa1020/CSS-Synthesizer-/issues/26) | 左右・上下の表示反転と独立座標照合 | [反転](issue-26.md) |
| [#27](https://github.com/furukawa1020/CSS-Synthesizer-/issues/27) | 値・時計を保持した集中表示 | [描画を広く](issue-27.md) |
| [#28](https://github.com/furukawa1020/CSS-Synthesizer-/issues/28) | Invoker Commandsで開閉する操作ガイドDialog | [Dialog](issue-28.md) |
| [#29](https://github.com/furukawa1020/CSS-Synthesizer-/issues/29) | Anchor Positioning付きパラメータ説明Popover | [その場の説明](issue-29.md) |
| [#30](https://github.com/furukawa1020/CSS-Synthesizer-/issues/30) | 選択モデルに対応するネイティブMathML | [数式の表示](issue-30.md) |
| [#31](https://github.com/furukawa1020/CSS-Synthesizer-/issues/31) | 指定値で停止して開く4つの静的プリセット | [プリセット](issue-31.md) |
| [#32](https://github.com/furukawa1020/CSS-Synthesizer-/issues/32) | 生成失敗時の前回ビルド保持 | [ビルドの更新](issue-32.md) |
| [#33](https://github.com/furukawa1020/CSS-Synthesizer-/issues/33) | 展開せずに内容・整合性を検査する配布ZIP CLI | [配布検査](issue-33.md) |
| [#34](https://github.com/furukawa1020/CSS-Synthesizer-/issues/34) | ID・Invoker／Popover・同梱ページ間の参照監査 | [参照監査](issue-34.md) |
| [#35](https://github.com/furukawa1020/CSS-Synthesizer-/issues/35) | システム色と実borderを使う強制カラー用表示 | [強制カラー](issue-35.md) |
| [#36](https://github.com/furukawa1020/CSS-Synthesizer-/issues/36) | 現在の形・値・時計・式を出す印刷用CSS | [印刷](issue-36.md) |

## 5つのモデル

共通で`u=i/(N−1)`、`θ=2πu`。振幅は`A`、位相は`φ`、時計は`t`とし、両軸を同じ`0.44 × 描画領域の短辺`で画面へ写す。`k`は形の反復であり、自動再生の速度ではない。

| モデル | 正規化座標 | 操作の意味 |
| --- | --- | --- |
| リサージュ | `x=A sin(kθ+φ+t)`、`y=A sin(2θ+t)` | kは横軸側の反復。位相は横軸、大きさは両軸へ作用 |
| 波形 | `x=2u−1`、`y=A sin(kθ+φ+t)` | kは左から右までの周期数。振幅は高さだけを変える |
| 花弁 | `r=A sin(kθ+φ)`、`x=r cos(θ+t)`、`y=r sin(θ+t)` | kと位相は半径の振動。時計は形全体を回転させる |
| 渦巻き | `r=A u`、`α=kθ+φ+t`、`x=r cos α`、`y=r sin α` | kは巻き数。位相と時計は全体の回転、大きさは両軸へ作用 |
| 合成軌道 | `x=A(0.65cos(θ+t)+0.35cos(kθ+φ−t))`、`y=A(0.65sin(θ+t)−0.35sin(kθ+φ−t))` | kと位相は副円側。主円65%と副円35%を合成する |

リサージュ・花弁・合成軌道は非整数kで開く場合がある。渦巻きは中心から外端へ向かう開いた曲線。いずれも点列として描き、常に閉曲線になるとは扱わない。

kは1.00〜8.00、位相は0〜360°、振幅は25〜100%。表示と描画は共通の有効値を使い、それぞれ0.01・1°・1%へ丸める。モデルごとに入力の名称と説明を切り替える。

## 確認した範囲

[ブラウザ検証](validation.md)には5モデル全192点の独立照合、反転、点の太さ、プリセット、集中表示、Dialog／Popover、MathML、小画面幅、強制カラー・印刷のCSS分岐を記録する。CSS分岐のfixtureを、実OSや実際の印刷の検証として扱わない。

配布物は7ページと2つのCSSへ束ねる。表示・描画・操作はHTML/CSSで実行し、通信・外部フォント・Canvas・SVG信号描画・WebAssembly・polyfillは使わない。

HTML-in-CanvasのAPI実装は、この20件に含めて実装済みと数えていない。技術としての依頼を[Issue #12](https://github.com/furukawa1020/CSS-Synthesizer-/issues/12)で管理し、JS描画を必要とする現行APIとJSゼロ指定の衝突を残す。実機・OS・読み上げ・他ブラウザ・性能などの受け入れは[Issue #3](https://github.com/furukawa1020/CSS-Synthesizer-/issues/3)を継続する。
