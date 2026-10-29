# 続く20件 — Issue #97〜#116

2026-10-30（日本時間）。前回の[20件](../batch40/README.md)に続き、同じ条件で曲線を比較し、入力の基準値と曲線の向きを確かめる機能を追加する。要件・実装・観測・未検証の事項を区別し、個々のUIに対するユーザー承認と同一視しない。

## Issueと実装

| Issue | 内容 | 要件と検査範囲 |
| --- | --- | --- |
| [#97](https://github.com/furukawa1020/CSS-Synthesizer-/issues/97) | 同じ入力と時計の比較画面 | [記録](issue-97.md) |
| [#98](https://github.com/furukawa1020/CSS-Synthesizer-/issues/98) | 8モデルから比較図を選択 | [記録](issue-98.md) |
| [#99](https://github.com/furukawa1020/CSS-Synthesizer-/issues/99) | 各96/192点の比較ページ | [記録](issue-99.md) |
| [#100](https://github.com/furukawa1020/CSS-Synthesizer-/issues/100) | 比較図と共有値の印刷CSS | [記録](issue-100.md) |
| [#101](https://github.com/furukawa1020/CSS-Synthesizer-/issues/101) | 反復の整数目盛りリンク | [記録](issue-101.md) |
| [#102](https://github.com/furukawa1020/CSS-Synthesizer-/issues/102) | 位相の90°刻みリンク | [記録](issue-102.md) |
| [#103](https://github.com/furukawa1020/CSS-Synthesizer-/issues/103) | 振幅の基準値リンク | [記録](issue-103.md) |
| [#104](https://github.com/furukawa1020/CSS-Synthesizer-/issues/104) | 任意の目盛り吸着 | [記録](issue-104.md) |
| [#105](https://github.com/furukawa1020/CSS-Synthesizer-/issues/105) | 位相φのラジアン換算表示 | [記録](issue-105.md) |
| [#106](https://github.com/furukawa1020/CSS-Synthesizer-/issues/106) | 軌跡の反時計回り回転 | [記録](issue-106.md) |
| [#107](https://github.com/furukawa1020/CSS-Synthesizer-/issues/107) | 等方的な表示倍率 | [記録](issue-107.md) |
| [#108](https://github.com/furukawa1020/CSS-Synthesizer-/issues/108) | 極座標の角度目盛り | [記録](issue-108.md) |
| [#109](https://github.com/furukawa1020/CSS-Synthesizer-/issues/109) | atan2()による接線矢印 | [記録](issue-109.md) |
| [#110](https://github.com/furukawa1020/CSS-Synthesizer-/issues/110) | CSS構文の診断ページ | [記録](issue-110.md) |
| [#111](https://github.com/furukawa1020/CSS-Synthesizer-/issues/111) | 新3モデルの停止プリセット | [記録](issue-111.md) |
| [#112](https://github.com/furukawa1020/CSS-Synthesizer-/issues/112) | 8モデルの個別解説 | [記録](issue-112.md) |
| [#113](https://github.com/furukawa1020/CSS-Synthesizer-/issues/113) | 外部manifestの全ファイル記述照合 | [記録](issue-113.md) |
| [#114](https://github.com/furukawa1020/CSS-Synthesizer-/issues/114) | 座標観測の一括CLI | [記録](issue-114.md) |
| [#115](https://github.com/furukawa1020/CSS-Synthesizer-/issues/115) | モデル定義・描画・checkerの対応検査 | [記録](issue-115.md) |
| [#116](https://github.com/furukawa1020/CSS-Synthesizer-/issues/116) | 保存観測のCI再照合と20件の統合 | [記録](issue-116.md) |

各PRの対応とマージ状態はIssueから追跡する。[統合検証](validation.md)には実際のブラウザ、画面条件、観測値、未検証範囲を記録する。

## 同じ入力で比較する

compare.htmlは各96点、compare-192.htmlは各192点。同じ反復k・位相φ・振幅A・自動時計tを各モデルへ渡す。既定の2図はリサージュと波形で、8モデルから表示する図を複数選べる。全解除時は図を選ぶ案内を示す。点のHTMLは8モデル分残り、非表示を計算量削減や性能合格とは扱わない。

3つの入力と時計を外側のlabが持ち、内側の各図が同じ有効値を継承する。既存CSSのモデル式を再利用する。同じ数値でもk・φ・Aの意味は各モデルで異なり、図の説明で確認できる。数式の一覧は[8モデルの仕様](../batch40/README.md)を参照。

比較の印刷CSSは選択図と共有値を残し、時計を停止する。inputのscroll timelineの箱は保持する。実際の印刷プレビュー・PDF・紙面はCSS分岐と別に評価する。

## 入力と表示の意味

反復1〜8、位相0/90/180/270/360°、振幅25/50/75/100%には目盛りリンクを設ける。native fragment navigationで帯を実際に移す。従来の連続調整を保ち、任意の吸着では反復整数・位相90°・振幅5%の目盛りに寄せる。吸着へ切り替えたときに位置が移り得る。

位相φは度または小数3桁のラジアン換算で読む。帯と目盛りリンクは度のままで、描画に使うφの精度は1°刻み。ラジアンの桁数を入力精度の増加とは扱わない。24秒で1周する自動時計tとは別の値。

単独画面の表示回転は0/45/90/180°で、数理座標の反時計回りを正とする。反転→回転の順にplotへ適用し、参照軸は固定。50/75/100%はAと別の表示倍率で、縦横同じ倍率で縮小する。回転では端の点が描画領域外へ出る場合がある。

極座標の角度は右0°、上90°、45°刻み。狭いfigureでは8方向の図外凡例へ切り替え、文字拡大で重ならないようにする。接線矢印はuが進む方向で、時間の速度ベクトルではない。CSSで解析的微分に比例するベクトルとatan2(-dy,dx)を計算し、塗りの方向に使う。微分がほぼ0では矢印を隠す。フェルマーの始点は比例ベクトルの片側極限で方向を定める。点の中心座標とは別に方向を照合する。

## 仕組みを調べる

features.htmlは18のCSS条件を実際の@supportsで判定する。構文対応は実動作保証ではない。@propertyの登録・継承・補間、Invoker Commandsの開閉、@starting-style、MathMLの読み上げなどは手動確認と明記する。

モデル別detailsでは、現在の選択モデルと独立に、8モデルの入力の意味・MathML・境界条件を読める。新しいフェルマー・減衰波・定在波の3プリセットを加え、10件で全8モデルを含む。すべてt=0で停止して始まり、ギャラリーは各96点。ページ移動時の値・時計の保持や状態保存は保証しない。

## 生成・配布・観測の検査

外部manifestの全ファイル名・バイト数・SHA-256とメタデータの形式をZIPと照合する。ハッシュは発行者の署名ではない。モデルレジストリとCSS・独立checkerの対応も生成候補で検査し、モデル名だけが追加されて基底の式が誤って出ることを防ぐ。この対応検査そのものは数式の証明ではない。

座標の一括CLIは、manifestで列挙した同じディレクトリの観測を順に独立式へ通す。欠落・重複・不正な参照や1件の照合失敗でも非ゼロ終了する。CIの保存観測再照合は回帰検査であり、ブラウザを再操作する検査ではない。

現行の配布は17 HTML・2 CSSの19アプリファイル、README.txtとSHA256SUMSを含む21 ZIPエントリー。開発ソース・QA fixture・観測資料はZIPへ入れない。

実機・OS・読み上げ・他ブラウザ・性能等は[Issue #3](https://github.com/furukawa1020/CSS-Synthesizer-/issues/3)へ残す。HTML-in-Canvas本体はJSゼロと衝突し、[Issue #12](https://github.com/furukawa1020/CSS-Synthesizer-/issues/12)で継続する。今回も公開デプロイやGitHub Releaseの発行を行わない。
