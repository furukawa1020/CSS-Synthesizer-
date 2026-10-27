# CSS Visual Synthesizer

HTML / CSSだけで、数式の形を選び、変え、止める視覚シンセサイザー。

**JavaScriptは開発用も含めて使用しません。** 現在のソース・配布物にJS / TS・Node依存はなく、生成・監査・テスト・配布はPython標準ライブラリで行います。作品の実行にはPythonも不要です。

リポジトリ：<https://github.com/furukawa1020/CSS-Synthesizer->。

## 触る

開発時はPython 3.11以上とGitを使います。追加パッケージのインストールは不要です。

```sh
python3 -m tools.build
python3 -m unittest discover -s tests -v
python3 -m tools.audit
python3 -m tools.serve
```

<http://127.0.0.1:3000>を開きます。

1. リサージュ・波形・花弁・渦巻き・合成軌道から形を選ぶ。
2. 横スクロール帯で反復・位相・振幅を調整する。帯を選んで左右キーでも動かせます。両端の矢印はページ送りで、一定の数値刻みではありません。
3. 気に入った形で時間を停止する。停止中も形を編集でき、再生すると続きから動きます。

「表示設定」では補助線、点の太さ、描画の配色、左右・上下反転、図中の説明を選べます。「描画を広く」は調整欄を畳む表示切り替えで、同じ場所の「調整に戻る」で解除します。HTMLのDialogとPopoverによる説明、MathMLの数式も参照できます。

4つのプリセットは、値を定めた別のHTMLページです。開くと指定値で停止した状態から始まります。現在の操作を保存する機能ではなく、ページ移動時の値・時間の保持も保証しません。通常の再読み込みも初期化操作としては案内していません。

## 配布する・検査する

変更をコミットしたソースから生成します。

```sh
python3 -m tools.package
python3 -m tools.verify dist/css-synthesizer-v0.1.zip --manifest dist/css-synthesizer-v0.1.manifest.json
```

ZIPは9つのHTML/CSS、使い方、SHA-256一覧を含む11ファイルです。検査CLIは展開せず、内容・参照先・改変・危険なエントリーを検査します。SHA-256は発行者の署名ではありません。[配布手順と検査範囲](docs/distribution.md)を参照してください。公開・デプロイ・GitHub Releaseの発行はこの手順に含みません。

ブラウザの印刷機能を使うと、形と現在の値・式を印刷向けに表示します。CSS分岐の検証は済んでいますが、実際の印刷ダイアログや紙面出力は未検証です。

## ソースと検証

- `src/page.html`・`src/fragments/`：HTMLの画面と説明。
- `src/models.json`・`src/presets.json`：モデルの名称・入力の意味・式と、プリセットの初期値。
- `src/style.css`・`src/styles/`、`src/engine.css`・`src/engines/`：画面と描画。ビルド時に2つのCSSへ合成します。
- `tools/`・`tests/`：Python標準ライブラリによる生成・静的監査・独立座標照合・配布検査。
- `qa/evidence/`：ブラウザの観測資料。配布ZIPには入れません。

候補を生成・監査してから`build/`を置き換えるため、通常の生成エラーで前回のビルドを先に削除しません。配置は二段階のrenameであり、電源断耐性や配信中の完全な原子性を保証するものではありません。

[20件の実装一覧](docs/batch20/README.md)、[今回のブラウザ検証](docs/batch20/validation.md)、[受け入れ状況](docs/acceptance.md)に範囲と証跡をまとめています。Chrome 155の観測とCSS fixtureを、実機タッチ・実OS・読み上げ・他ブラウザ・一般端末の性能の合格には置き換えていません。残る検証は[Issue #3](https://github.com/furukawa1020/CSS-Synthesizer-/issues/3)で管理します。

`python3 -m tools.fixtures`は検証専用HTML/CSSを生成します。次の正常なビルドで削除され、配布物には入りません。96 / 192 / 384点は比較用であり、最適な点数や性能合格を示すものではありません。

## 設計資料

- [要件定義](docs/requirements.md)と[デザインブリーフ](docs/design-brief.md)
- [モデルと機能の現在の一覧](docs/batch20/README.md)／[初期の数理モデル・入力案](docs/math-and-input.md)
- [作業計画と残件](docs/plan.md)
- [JavaScript全面撤去の判断](docs/decisions/0003-zero-javascript.md)
- [HTML-in-Canvasの採用調査](docs/research/html-in-canvas.md)

HTML-in-Canvasは技術としての採用依頼ですが、現行APIのJS描画と以前のJSゼロ指定が衝突しています。API本体は未実装で、例外範囲と実測を[Issue #12](https://github.com/furukawa1020/CSS-Synthesizer-/issues/12)に残しています。

過去のコミットには撤去前のNode開発用コードが残ります。履歴を改変してJSゼロに見せることはせず、現在のソースと配布物をゼロにしています。旧試作のUI・コード・配信先は引き継いでいません。
