# 比較表示と時計の20件 — Issue #137〜#156

2026-10-31（日本時間）。継続実装依頼から以下の20件を選び、Issueを先に作成した。個々のUIにユーザー承認があったとは扱わない。各PRとマージ状態はIssueから追跡する。

| Issue | 要件 | 記録 |
| --- | --- | --- |
| [#137](https://github.com/furukawa1020/CSS-Synthesizer-/issues/137) | 比較画面で補助線と図中の説明を共有する | [変更と検査](issue-137.md) |
| [#138](https://github.com/furukawa1020/CSS-Synthesizer-/issues/138) | 比較画面で点の太さと形を揃える | [変更と検査](issue-138.md) |
| [#139](https://github.com/furukawa1020/CSS-Synthesizer-/issues/139) | 比較画面で配色と描画順の色を共有する | [変更と検査](issue-139.md) |
| [#140](https://github.com/furukawa1020/CSS-Synthesizer-/issues/140) | 比較画面で描画範囲と端点を揃える | [変更と検査](issue-140.md) |
| [#141](https://github.com/furukawa1020/CSS-Synthesizer-/issues/141) | 比較図すべてに同じ左右上下の反転を適用する | [変更と検査](issue-141.md) |
| [#142](https://github.com/furukawa1020/CSS-Synthesizer-/issues/142) | 比較図すべてに同じ反時計回り回転を適用する | [変更と検査](issue-142.md) |
| [#143](https://github.com/furukawa1020/CSS-Synthesizer-/issues/143) | 比較図すべてに同じ表示倍率を適用する | [変更と検査](issue-143.md) |
| [#144](https://github.com/furukawa1020/CSS-Synthesizer-/issues/144) | 比較図の描画領域比率を揃える | [変更と検査](issue-144.md) |
| [#145](https://github.com/furukawa1020/CSS-Synthesizer-/issues/145) | 比較の共有位相にもラジアン換算を表示する | [変更と検査](issue-145.md) |
| [#146](https://github.com/furukawa1020/CSS-Synthesizer-/issues/146) | 比較モデルの既定選択へ戻す操作と選択数を追加する | [変更と検査](issue-146.md) |
| [#147](https://github.com/furukawa1020/CSS-Synthesizer-/issues/147) | 比較図を縦一列でも読めるようにする | [変更と検査](issue-147.md) |
| [#148](https://github.com/furukawa1020/CSS-Synthesizer-/issues/148) | 点の不透明度を形と独立に調整する | [変更と検査](issue-148.md) |
| [#149](https://github.com/furukawa1020/CSS-Synthesizer-/issues/149) | 補助線の濃さを標準と強めから選ぶ | [変更と検査](issue-149.md) |
| [#150](https://github.com/furukawa1020/CSS-Synthesizer-/issues/150) | 自動時計の周期を12秒24秒48秒から選ぶ | [変更と検査](issue-150.md) |
| [#151](https://github.com/furukawa1020/CSS-Synthesizer-/issues/151) | 自動時計を逆方向にも再生する | [変更と検査](issue-151.md) |
| [#152](https://github.com/furukawa1020/CSS-Synthesizer-/issues/152) | プリセット一覧をモデル別に絞り込む | [変更と検査](issue-152.md) |
| [#153](https://github.com/furukawa1020/CSS-Synthesizer-/issues/153) | プリセット一覧で数値だけの表示も選べるようにする | [変更と検査](issue-153.md) |
| [#154](https://github.com/furukawa1020/CSS-Synthesizer-/issues/154) | 座標照合で全点の観測を要求できるようにする | [変更と検査](issue-154.md) |
| [#155](https://github.com/furukawa1020/CSS-Synthesizer-/issues/155) | 接線照合にも境界付きmanifest一括検査を追加する | [変更と検査](issue-155.md) |
| [#156](https://github.com/furukawa1020/CSS-Synthesizer-/issues/156) | 比較表示と時計の20件を統合検証してCIへ記録する | [変更と検査](issue-156.md) |

## 比較画面の表示操作

単独画面のHTML断片とCSSを共用し、補助線・説明、点の太さ/形、配色/順序色、範囲/端点、反転・回転・倍率・領域比率を選べる。内側labの変数の初期化を解決し、同じ外側設定を全モデルへ継承する。反転→等方倍率→反時計回り回転の意味と、固定の参照軸は変わらない。単独と同じ位相φのラジアン換算と任意の吸着を比較へ加えた。

モデル選択は専用formのnative resetで既定の2モデルへ戻す。入力・時計・表示設定はフォーム外に置く。入力を初期化する操作ではない。CSS counterの選択数は描画可能数や性能の指標ではない。「幅に合わせる/縦一列」はscreenの配置だけを選ぶ。印刷は既存の2列。

## 時計と塗り

時計周期は既定24秒、12/48秒も選べる。順方向/逆方向は時計のanimation-directionだけに適用し、3入力のtimelineは通常方向のまま。周期/方向の切替で時計位置は移り得る。停止・端末に従う・明示再生は既存のclock-stateを使う。逆再生でも接線は点の並びuが進む方向で、時間の速度ではない。

点の不透明度25/50/100%は範囲のmaskと乗算し、点中心やAを変えない。接線の微分ゼロによる塗りの非表示も別に維持する。補助線の「強め」はcolor-mix対応時に選べ、配色の文字色から線色を作る。未対応では標準線。強制カラー/印刷では点の不透明度を100%にし、選択範囲は維持する。

## 一覧と検査

形の一覧は全件/8モデルで絞れ、「図と値/値だけ」も選べる。すべてのHTMLは残り、性能改善や計算点削減の主張には使わない。:has非対応では全件の図と値を表示する。リンクは既存の192点・時計0で始まるプリセットへ移動する。編集状態の保存やページ間の保持は保証しない。

座標CLIの--require-allは0〜count−1の全観測を要求する。既定は部分観測を許容して旧呼び出しを保つ。接線CLIにも--batchを追加し、座標と同じ境界付きmanifestローダーを共用する。角度誤差はCSS pxと区別してmax_error_degreesで集計する。保存データの再照合はライブのブラウザテストではない。

[統合検証](validation.md)に今回22ケース・2,304点の座標と同数の接線方向、操作、幅と文字拡大、CSSメディア分岐を記録する。実行・開発ともJSゼロ。配布は17 HTML・2 CSS、README.txtとSHA256SUMS込み21エントリー。

実機・OS・読み上げ・他ブラウザ・性能・実印刷等は[Issue #3](https://github.com/furukawa1020/CSS-Synthesizer-/issues/3)、HTML-in-Canvas本体とJSゼロの衝突は[Issue #12](https://github.com/furukawa1020/CSS-Synthesizer-/issues/12)に残す。公開デプロイやGitHub Releaseは行わない。以前の記録は[前回20件](../batch60/README.md)へ。
