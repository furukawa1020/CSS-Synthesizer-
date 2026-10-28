# 追加20件 — Issue #57〜#76

2026-10-29（日本時間）の追加実装。前回の[20件](../batch20/README.md)に続く20件を、各Issueの要件から実装・検査・日本語PRへ進める。機能が実装されていること、特定環境で観測できたこと、ユーザーが個々のUIの好みを承認したことは区別する。

## Issueと実装

| Issue | 内容 | 要件・検査範囲 |
| --- | --- | --- |
| [#57](https://github.com/furukawa1020/CSS-Synthesizer-/issues/57) | sqrt()によるフェルマー渦巻き | [記録](issue-57.md) |
| [#58](https://github.com/furukawa1020/CSS-Synthesizer-/issues/58) | exp()による減衰波 | [記録](issue-58.md) |
| [#59](https://github.com/furukawa1020/CSS-Synthesizer-/issues/59) | 定在波 | [記録](issue-59.md) |
| [#60](https://github.com/furukawa1020/CSS-Synthesizer-/issues/60) | 始点と終点の印 | [記録](issue-60.md) |
| [#61](https://github.com/furukawa1020/CSS-Synthesizer-/issues/61) | 描画順の色分け | [記録](issue-61.md) |
| [#62](https://github.com/furukawa1020/CSS-Synthesizer-/issues/62) | 丸・四角・菱形の点 | [記録](issue-62.md) |
| [#63](https://github.com/furukawa1020/CSS-Synthesizer-/issues/63) | 先頭25%・50%・全点の表示 | [記録](issue-63.md) |
| [#64](https://github.com/furukawa1020/CSS-Synthesizer-/issues/64) | 正規化座標の目盛り | [記録](issue-64.md) |
| [#65](https://github.com/furukawa1020/CSS-Synthesizer-/issues/65) | 自動・正方形・16:9の領域 | [記録](issue-65.md) |
| [#66](https://github.com/furukawa1020/CSS-Synthesizer-/issues/66) | 時計の位置を度で表示 | [記録](issue-66.md) |
| [#67](https://github.com/furukawa1020/CSS-Synthesizer-/issues/67) | Dialog／Popoverの開閉トランジション | [記録](issue-67.md) |
| [#68](https://github.com/furukawa1020/CSS-Synthesizer-/issues/68) | 描画付近の点数ナビゲーション | [記録](issue-68.md) |
| [#69](https://github.com/furukawa1020/CSS-Synthesizer-/issues/69) | 可変プリセットレジストリ | [記録](issue-69.md) |
| [#70](https://github.com/furukawa1020/CSS-Synthesizer-/issues/70) | 花弁・渦巻き・合成軌道のプリセット | [記録](issue-70.md) |
| [#71](https://github.com/furukawa1020/CSS-Synthesizer-/issues/71) | 7図を比較する静的ギャラリー | [記録](issue-71.md) |
| [#72](https://github.com/furukawa1020/CSS-Synthesizer-/issues/72) | JSONの重複キー・非有限数を拒否 | [記録](issue-72.md) |
| [#73](https://github.com/furukawa1020/CSS-Synthesizer-/issues/73) | ソース全体のJSゼロ検査 | [記録](issue-73.md) |
| [#74](https://github.com/furukawa1020/CSS-Synthesizer-/issues/74) | CSSエスケープの外部参照監査 | [記録](issue-74.md) |
| [#75](https://github.com/furukawa1020/CSS-Synthesizer-/issues/75) | buildを変更しない鮮度検査 | [記録](issue-75.md) |
| [#76](https://github.com/furukawa1020/CSS-Synthesizer-/issues/76) | ZIP検査のCI実行と統合検証 | [記録](issue-76.md) |

PRとマージの対応は各Issueで追跡する。[統合検証](validation.md)にはブラウザ・画面条件・測定値と未検証範囲を記録する。

## 8モデルの数式

共通にu=i/(N−1)、θ=2πu。kは反復または巻き数、φは入力の位相、Aは振幅、tは自動時計のラジアン値。画面座標は中心を原点に短辺の44%を1として縦横等倍率で描く。

| モデル | 数式 | 読み方 |
| --- | --- | --- |
| リサージュ | x=A sin(kθ+φ+t)、y=A sin(2θ+t) | kは横軸側の反復数 |
| 波形 | x=2u−1、y=A sin(kθ+φ+t) | kは左右端間の周期数。Aは横幅を変えない |
| 花弁 | r=A sin(kθ+φ)、x=r cos(θ+t)、y=r sin(θ+t) | 符号付きの半径。時間は全体を回転させる |
| 渦巻き | r=A u、α=kθ+φ+t、x=r cosα、y=r sinα | 半径はuに比例。中心から外へ開く |
| 合成軌道 | x=A[0.65 cos(θ+t)+0.35 cos(kθ+φ−t)]、y=A[0.65 sin(θ+t)−0.35 sin(kθ+φ−t)] | 主円65%・副円35%。時間は全体の回転 |
| フェルマー渦巻き | r=A sqrt(u)、α=kθ+φ+t、x=r cosα、y=r sinα | 半径はuの平方根。通常の渦巻きより中心から早く広がる |
| 減衰波 | x=2u−1、y=A exp(−3u) sin(kθ+φ+t) | 減衰率3は固定。右端の包絡振幅は左端の約5% |
| 定在波 | x=2u−1、y=A sin(kθ+φ) cos(t) | 空間の節を保って上下に振動。一般のk・φで固定端境界を保証しない |

kは1.00〜8.00、位相は0〜360°、振幅は25〜100%。表示と描画は同じ丸め済み値を使う。非整数kなどで閉曲線にならないモデルがある。sqrt()・exp()の必要なモデルは個別に構文の対応を検出し、非対応では当該モデルの選択・描画を制限して理由を示す。

## 表示と状態の意味

端点の○はu=0、□はu=1。閉じた曲線では重なる場合がある。描画順の色はu=0→1を示し、時間や速さではない。点の形・太さ・表示範囲は数式と点中心を変更しない。先頭25%・50%はuの上限で可視性を変えるため、点の配置と計算数は維持する。

座標目盛りは−1・0・+1の正規化座標で、反転は軌跡に適用する。領域の比率は自動・1:1・16:9から選ぶ。時計の位置は1周24秒を度へ換算した整数表示で、入力の位相φとは別。周期末尾は丸めで360°を示し、次周期で0°に戻る。

7つのプリセットはt=0で停止した192点の別ページ。「形の一覧」は各96点で同じ初期状態を比較する。保存機能はなく、点数やプリセットへ移動した際の状態保持も保証しない。

## 開発と配布

プリセットの定義は1〜24件を許容し、名前とpreset-*.htmlを一意に検査する。現在は7件。生成・監査・配布は`tools.assets`の同じファイル定義を使い、現行配布は11 HTML・2 CSSの13アプリファイル、README.txt・SHA256SUMSを含む15 ZIPエントリー。

`tools.source_audit`は現在の実装関連ファイルを検査する。Git履歴・文書・既知の生成物・外部ワークツリーまで検査するものではない。CSS参照の監査は作品専用の静的ガードであり、CSS全体を安全化する汎用サニタイザーではない。

JSONの曖昧な入力を拒否し、生成候補を監査した後にbuildへ配置する。`tools.build --check`は候補とのファイル名・全バイトを比較し、既存buildを変更しない。CIでは生成ZIPを外部manifest付きで`tools.verify`へ通す。ハッシュの整合性検査を発行者の認証・署名とは扱わない。

JavaScriptゼロを維持している。HTML-in-Canvas本体は未実装で[Issue #12](https://github.com/furukawa1020/CSS-Synthesizer-/issues/12)、実機・OS・読み上げ・性能・他ブラウザ等は[Issue #3](https://github.com/furukawa1020/CSS-Synthesizer-/issues/3)で継続する。
