# Issue #7：開発用を含むJavaScript撤去

検証日：2026-10-27（日本時間）。対象ブランチ：`issue-7/zero-javascript`。現在のツリーを検査し、履歴中の旧ソースは消していない。

## 撤去と置き換え

7つのJS/Node関連ファイルを削除した。ビルド・監査・ローカル配信・QA fixture・座標照合・配布をPython標準ライブラリへ移した。追加パッケージのインストールは不要。

CIはGitで対象コミットを取得し、Pythonで実行する。Nodeのセットアップと、Node製のcheckout actionを使わない。GitHubサービスやブラウザの内部実装が何であるかまでゼロを主張しない。

## ローカル確認

```sh
python3 -m tools.build
python3 -m unittest discover -s tests -v
python3 -m tools.audit
python3 -m tools.package
```

監査13件、独立座標3件、配布5件、生成・配信・JSゼロ3件の計24テストが対象。配布CLIはclean HEADで再実行し、現在のソースを再ビルドしてから生成することを確認する。JS/TSソースとNode manifestの再混入はテストを失敗にする。

5つの配布HTML/CSSを監査する。監査は本プロジェクト用の静的ガードであり、任意のHTML/CSSの安全性を保証する汎用サニタイザーではない。

## 境界

作品で計算するのはCSSの入力・座標・時間。Pythonは事前生成と開発用検証だけに使い、配布ページへ配信しない。ブラウザ検証の読み取りは検証用サービスで行い、観測値をJSONとして保存する。作品には検証用スクリプトも埋め込まない。

この移行によって、実機タッチ、OS設定、他ブラウザや性能の未検証事項が解消するわけではない。それらはIssue #3で管理する。
