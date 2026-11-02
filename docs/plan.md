# 作業計画と現在地

更新：2026-11-02（日本時間）。第8回の20件はIssue #297〜#316。前回のPR #277〜#296はmainへ統合済み。先にIssueを作り、Issue別ブランチ・日本語PR・対象headのCI成功後のマージで進める。

新4モデル、停止プリセット、点の観察、原点と基準円、極グリッド、表示変換、保存時計を扱う。[第8回の一覧](batch160/README.md)、[数式と表示](batch160/drawing.md)、[検証と制限](batch160/validation.md)。前回の[座標加工20件](batch120/README.md)も保持する。

HTML/CSSのみ、開発もPython標準ライブラリのみ。JS/TS/Node、Canvas/SVG描画、左色線の付箋カード・強い影・丸いカード列を加えない。非表示・間引きを性能合格として扱わない。音声・自由配線・ブラウザー内の永続保存・アカウント・公開デプロイ・GitHub Releaseは範囲外。

## 継続するIssue

- #3：実機タッチ、実OS、読み上げ、他ブラウザー、性能、UIズーム、file://、ライブ周期境界、実印刷。
- #12：HTML-in-Canvas現行APIのJS描画とJSゼロ指定の衝突。描画本体は未実装。

保存JSON再照合とライブ操作、iframeと実端末、印刷CSSと実印刷を区別する。前回の[第5回](batch100/README.md)、[第4回](batch80/README.md)、[第3回](batch60/README.md)、[第2回](batch40/README.md)、[第1回](batch20/README.md)は履歴として保持する。
