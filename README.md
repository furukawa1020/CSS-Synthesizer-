# CSS Visual Synthesizer

HTML / CSSだけで、操作から模様を作る視覚シンセサイザー。

**JavaScriptは開発用も含めて使用しません。** 現在のソースにJS / TSファイル、package.json、Node依存はありません。生成・監査・テスト・配布はPython標準ライブラリだけで実行します。作品の実行にはPythonも不要です。

リポジトリ：<https://github.com/furukawa1020/CSS-Synthesizer->。

## 動かす

開発用にPython 3.11以上を使います。追加パッケージのインストールは不要です。

```sh
python3 -m tools.build
python3 -m unittest discover -s tests -v
python3 -m tools.audit
python3 -m tools.serve
```

<http://127.0.0.1:3000>を開きます。リサージュ／波形を選び、横スクロール帯で反復・位相・振幅を変え、時間を停止・再開できます。両端の矢印はブラウザのページ送りで、一定の数値刻みではありません。

コミット済みのソースから配布ZIPを作る場合：

```sh
python3 -m tools.package
```

現在のソースを再ビルドし、`dist/css-synthesizer-v0.1.zip`と生成元・SHA-256のmanifestを作ります。[配布手順](docs/distribution.md)を参照してください。外部への公開・デプロイは行いません。

[画面の設計と4状態](docs/validation/issue-2.md)、[受け入れ状況](docs/acceptance.md)に検証の範囲をまとめています。

## 構成と検証

- `src/`：HTML / CSSの作品。通信、外部フォント、Canvas、SVG信号描画、WebAssemblyなし。
- `tools/`：Python標準ライブラリによる開発用ツール。
- `tests/`：Python unittest。JS/TSソースとNode manifestが再び入っていないかも検査。
- `qa/evidence/`：ブラウザの観測記録。配布ZIPには入れません。
- `build/`：生成物。`python3 -m tools.build`で作り直します。

QA用のHTML/CSSは`python3 -m tools.fixtures`で生成できます。次のbuildで削除されます。96 / 192 / 384点は比較用であり、最適な点数や性能合格を示すものではありません。

現行Chrome / Edge向けです。実機タッチ、読み上げの更新通知、実OSの動きを減らす設定、他ブラウザ、一般端末での性能は検証が残っています。

## 設計資料

1. [要件定義](docs/requirements.md)
2. [数理モデルと入力](docs/math-and-input.md)
3. [デザインブリーフ](docs/design-brief.md)
4. [技術検証計画](docs/technical-plan.md)
5. [受け入れ状況](docs/acceptance.md)
6. [作業計画](docs/plan.md)
7. [JavaScript全面撤去の判断](docs/decisions/0003-zero-javascript.md)
8. [HTML-in-Canvasの採用調査と要件衝突](docs/research/html-in-canvas.md)（Issue #12、API実装は未完了）

過去のコミットには、撤去前のNode開発用コードが残ります。履歴を改変してJSゼロに見せることはしません。現在のソースと配布物をゼロにしています。旧試作のUI・コード・配信先は引き継いでいません。
