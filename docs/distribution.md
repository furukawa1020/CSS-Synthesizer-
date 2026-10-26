# v0.1の静的配布物

この手順はZIPをローカルに生成する。公開・デプロイ・GitHub Releaseの発行は行わない。実機タッチ・他ブラウザ・性能等の未検証項目は[受け入れ記録](acceptance.md)と[Issue #3](https://github.com/furukawa1020/CSS-Synthesizer-/issues/3)で管理する。

## 生成する

Python 3とGitを使う。Pythonの標準ライブラリだけを使い、追加パッケージのインストールは不要。

```sh
python3 -m tools.build
python3 -m unittest discover -s tests
python3 -m tools.audit
python3 -m tools.package
```

`dist/css-synthesizer-v0.1.zip`と`dist/css-synthesizer-v0.1.manifest.json`を生成する。`python3 -m tools.package`単体でも、未コミット変更がないことを確認してから現在のソースを必ず再ビルドし、監査・ZIP生成へ進む。以前の`build/`とQA fixtureはこの再ビルドで削除される。

ZIPを展開し、HTMLとCSSを同じディレクトリに置く。現行Chrome / Edgeで`index.html`を開く。Pythonは作品の実行時には不要。配布ページも開発ツールもJavaScriptを使わない。

ZIPに入るものは、次の7ファイルだけである。

| ファイル | 役割 |
| --- | --- |
| index.html | 192点の作品 |
| samples-96.html | 96点の比較用ページ |
| samples-384.html | 384点の比較用ページ |
| style.css | 画面・操作の表示 |
| engine.css | 入力・数理モデル・時間 |
| README.txt | 展開後の使い方と制限の参照先 |
| SHA256SUMS | 5つのHTML/CSSのSHA-256一覧 |

配布APIの`package_release()`は5つのHTML/CSSを再監査してからZIPを作る。入力ディレクトリに余分なファイル、ディレクトリ、シンボリックリンクがある場合は失敗させる。CLIはこのAPIの前にビルドを実行する。開発用コード、検証用コード、ソース、Git情報をZIPへ入れない。

## 再現性と生成元

ZIPのファイル順・時刻・属性は固定し、圧縮なしのZIP STORE形式を使う。同じHTML/CSSなら、元ファイルの更新時刻や生成元commitが違ってもZIPのバイト列は同じになる。

生成元の完全なcommit SHAはZIPの外のmanifestに記録する。manifestはZIP全体のSHA-256と同梱全ファイルのSHA-256も持つ。生成日時は記録しない。これにより、ソースを追跡しつつZIP自体の再現性を維持する。

CLIは未コミット変更があると失敗させ、manifestにパッケージ実行時の`HEAD`を記録する。ZIPはそのソースから再生成した成果物だけを使う。SHA-256は改変の比較用で、発行者の署名や動作保証ではない。

## 確認範囲

`tests/test_package.py`はZIPの格納内容、既知のCRC-32、SHA-256一覧、同一入力の再現一致、入力変更の反映、QAファイル等の拒否、禁止スクリプトの拒否を確認する。CLIは未コミット変更のある環境では拒否を確認し、変更のない環境では古い生成物・QA fixtureを再生成で置き換えて現在のcommitを記録することを確認する。これは実ブラウザでの作品の操作・描画・性能の検証を置き換えない。
