# CSS Visual Synthesizer

HTML / CSSだけで、数式の形を選び、変え、止める視覚シンセサイザー。

**JavaScriptは開発用も含めて使用しません。** 現在のソース・配布物にJS / TS・Node依存はなく、生成・監査・テスト・配布はPython標準ライブラリで行います。作品の実行にはPythonも不要です。

リポジトリ：<https://github.com/furukawa1020/CSS-Synthesizer->。

## 触る

開発時はPython 3.11以上とGitを使います。追加パッケージのインストールは不要です。

```sh
python3 -m tools.source_audit
python3 -m tools.build
python3 -m tools.build --check
python3 -m unittest discover -s tests -v
python3 -m tools.audit
python3 -m tools.serve
```

<http://127.0.0.1:3000>を開きます。

1. リサージュ・波形・花弁・渦巻き・合成軌道・フェルマー渦巻き・減衰波・定在波から形を選ぶ。
2. 横スクロール帯で反復・位相・振幅を調整する。帯を選んで左右キーでも動かせます。各帯の目盛りリンクでは特定の基準値へ移動できます。両端の矢印はページ送りで、一定の数値刻みではありません。
3. 気に入った形で時間を停止する。停止中も形を編集でき、再生すると続きから動きます。

「表示設定」では補助線とその濃さ、点の太さ・形・不透明度・色分け、描画範囲、端点の印、配色、反転・回転・表示倍率、描画領域の比率、図中の説明を選べます。目盛りへの吸着と位相φのラジアン換算も任意で選べます。ラジアン表示にしても、入力の精度は1°刻みのままです。接線の矢印は点の並びuが進む方向で、時間方向の速度ベクトルではありません。描画範囲は先頭25%・50%・全点の表示選択で、非表示の点も座標計算と配置を保持します。計算点数を減らす操作ではありません。

「描画を広く」は調整欄を畳む表示切り替えで、「調整に戻る」で解除します。描画の下にある時計の位置は既定1周24秒の時間を角度で示した値で、入力の位相φとは別です。「時計の進み方」で12/24/48秒と順方向/逆方向を選べます。周期や方向の切替で時計位置は移り得ます。点数の96 / 192 / 384点へのリンクは別ページへの移動です。

`gallery.html`の「形の一覧」では、全件/モデル別の絞り込みと図/値だけの表示を選べます。10プリセットを各96点・時計t=0の静止図で比べられます。開いたプリセットは192点で、同じ値・停止状態から始まります。ページ移動時の入力や時間の保持は保証せず、操作状態を保存する機能ではありません。通常の再読み込みも初期化操作として案内していません。

`compare.html`では各96点、`compare-192.html`では各192点で、同じ3入力と時計を複数モデルへ渡します。既定の比較はリサージュと波形で、8モデルから表示する図を選べます。非表示の図もHTMLは残ります。点数や選択数を性能合格の指標とは扱いません。比較の表示設定で補助線・形・配色・範囲・反転・回転・倍率などを全図に揃えられます。選択モデルだけを既定の2つへ戻せ、入力・時計・表示設定は保ちます。縦一列配置も選べます。比較画面の印刷CSSも共有値と選択図を残します。

`features.html`では18のCSS条件の構文対応を`@supports`で表示します。構文判定と実動作は別です。@propertyの実動作、Invoker Commands、MathMLの読み上げなどは手動確認の項目です。

HTMLのDialog・PopoverとMathMLによる説明を参照できます。開閉の短いCSSトランジションは、端末の動きを減らす設定で解除します。

## 配布する・検査する

変更をコミットしたソースから生成します。

```sh
python3 -m tools.package
python3 -m tools.verify dist/css-synthesizer-v0.1.zip --manifest dist/css-synthesizer-v0.1.manifest.json
```

ZIPは17 HTML・2 CSSの19アプリファイル、使い方、SHA-256一覧を含む21ファイルです。検査CLIは展開せず、内容・参照先・改変・危険なエントリーを検査します。外部manifest指定では、ZIP全体のハッシュに加え、全同梱ファイルの名前・サイズ・ハッシュとメタデータの形式も照合します。SHA-256は発行者の署名ではありません。[配布手順と検査範囲](docs/distribution.md)を参照してください。公開・デプロイ・GitHub Releaseの発行はこの手順に含みません。

ブラウザの印刷機能を使うと、形と現在の値・式を印刷向けに表示します。CSS分岐の検証と実際の印刷プレビュー・PDF・紙への出力は区別しています。

## ソースと検証

- `src/page.html`・`src/fragments/`：HTMLの画面と説明。
- `src/models.json`・`src/presets.json`：8モデルの名称・入力の意味・式と、10プリセットの初期値。
- `src/style.css`・`src/styles/`、`src/engine.css`・`src/engines/`：画面と描画。ビルド時に2つのCSSへ合成します。
- `tools/`・`tests/`：Python標準ライブラリによる生成・ソース監査・HTML/CSS監査・独立座標照合・配布検査。
- `qa/evidence/`：ブラウザの観測資料。配布ZIPには入れません。

候補を生成・監査してから`build/`を置き換えるため、通常の生成エラーで前回のビルドを先に削除しません。配置は二段階のrenameであり、電源断耐性や配信中の完全な原子性を保証しません。`python3 -m tools.build --check`は現在のソースから候補を作って照合し、既存buildを変更せず鮮度を検査します。

最新の[20件の実装一覧](docs/batch80/README.md)、[ブラウザ検証](docs/batch80/validation.md)、[受け入れ状況](docs/acceptance.md)で実装と観測を分けています。前回の[20件](docs/batch60/README.md)と[その前の20件](docs/batch40/README.md)と[検証記録](docs/batch40/validation.md)、[最初の20件](docs/batch20/README.md)も残しています。実機タッチ・実OS・読み上げ・他ブラウザ・一般端末の性能などの残件は[Issue #3](https://github.com/furukawa1020/CSS-Synthesizer-/issues/3)で管理します。

`python3 -m tools.coordinates --batch 観測manifest.json`は、同じディレクトリの観測JSONを一覧から独立照合します。`--require-all`で全点が揃うことを要求できます。`tools.tangents`は接線方向の観測を別の数式で検査し、同じ形式の`--batch`も使えます。保存した有限ケースの再照合は全入力・全ブラウザの証明ではありません。

`python3 -m tools.fixtures`は検証専用HTML/CSSを生成します。次の正常なビルドで削除され、配布物には入りません。96 / 192 / 384点は比較用であり、最適な点数や性能合格を示しません。

## 設計資料

- [要件定義](docs/requirements.md)と[デザインブリーフ](docs/design-brief.md)
- [モデルと機能の現在の一覧](docs/batch60/README.md)／[初期の数理モデル・入力案](docs/math-and-input.md)
- [作業計画と残件](docs/plan.md)
- [JavaScript全面撤去の判断](docs/decisions/0003-zero-javascript.md)
- [HTML-in-Canvasの採用調査](docs/research/html-in-canvas.md)

HTML-in-Canvasは技術としての採用依頼ですが、現行APIのJS描画と以前のJSゼロ指定が衝突しています。API本体は未実装で、例外範囲と実測を[Issue #12](https://github.com/furukawa1020/CSS-Synthesizer-/issues/12)に残しています。

過去のコミットには撤去前のNode開発用コードが残ります。履歴を改変してJSゼロに見せず、現在のソースと配布物をゼロにしています。旧試作のUI・コード・配信先は引き継いでいません。
