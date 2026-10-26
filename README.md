# CSS Visual Synthesizer

HTML / CSSを使って、自分の操作から模様を作るブラウザ上の視覚シンセサイザー。

**状態：要件定義 draft 0.1 ＋ Issue #1の入力・数理コア検証。完成版のUIは未決定です。**

リポジトリ：<https://github.com/furukawa1020/CSS-Synthesizer->。ユーザーが作成した公開リポジトリを使用します。

前の試作とは履歴・ソース・配信先を分けた、新規リポジトリです。旧試作のUI、コード、架空のブランド、描画点数は引き継いでいません。この段階ではデプロイしません。

## 読む順序

1. [要件定義](docs/requirements.md)：何を作り、何を完成とするか
2. [数理モデルと入力](docs/math-and-input.md)：操作が何を変えるか
3. [デザインブリーフ](docs/design-brief.md)：UIの判断基準と未確定事項
4. [4状態のワイヤーフレーム](docs/design/wireframes.svg)：完成デザインではない構成案
5. [技術検証計画](docs/technical-plan.md)：CSSだけで成立するか、先に確かめること
6. [受け入れ条件](docs/acceptance.md)：要件と検証手順の対応
7. [作業計画と判断待ち](docs/plan.md)：実装へ進める順序

## 現時点の合意と仮定

| 区分 | 内容 |
| --- | --- |
| ユーザーから確定 | 最新の素のHTML / CSSの力を試す作品を作りたい |
| ユーザーから確定 | 題材はCSS視覚シンセサイザー |
| ユーザーから確定 | 前作のUIと進め方は不採用。ゼロからリポジトリを作り、要件定義を先に行う |
| 提案・未承認 | 主体験は「自分の操作で模様を作る」。技術解説は補助に置く |
| 提案・未承認 | 画面を大きく作品に使い、必要な操作だけを見せる |
| 提案・未承認 | ブラウザ内のアプリケーションコードはHTML / CSSのみ、JavaScriptは使わない |
| 提案・未承認 | 最初の完成対象はリサージュと波形の2モデル |

未承認の内容をユーザーの好み・合意として扱わないでください。

## リポジトリ構成

`src/`がHTML/CSSの検証画面、`scripts/`がNodeの生成・監査・ローカル配信、`tests/`が静的ガードのテスト、`qa/`がブラウザ検証用コードと記録です。`build/`は生成物でGitには含めません。

ブラウザに配信するアプリケーションはHTML/CSSのみです。Nodeは開発用です。npm依存パッケージ、フレームワーク、Canvas、SVGによる信号描画はありません。

## ローカルで動かす

Node 22以上を使用します。依存パッケージのインストールは不要です。

```sh
npm run build
npm test
npm run audit
npm run dev
```

表示されたローカルURLを開きます。リサージュ／波形の選択、横スクロール帯での反復・位相・振幅の調整、時間停止・再開を試せます。`＋−`はブラウザのページ送りであり、0.01ずつの増減ではありません。

`npm run build`は`build/`を作り直します。96/192/384点のページを生成しますが、最適な点数を決めたわけではありません。QA用ページを作る場合は続けて`node qa/create-fixtures.mjs`を実行します。QA用ページは次のbuildで削除されます。

## 検証と次の作業

- [入力コアの設計判断](docs/decisions/0002-css-input-core.md)
- [ブラウザ検証の結果と再現方法](docs/validation/issue-1.md)
- [Issue #1：入力・数理コア](https://github.com/furukawa1020/CSS-Synthesizer-/issues/1)
- [Issue #2：作品中心のUI設計](https://github.com/furukawa1020/CSS-Synthesizer-/issues/2)
- [Issue #3：実機・互換性・性能検証](https://github.com/furukawa1020/CSS-Synthesizer-/issues/3)

現行Chrome/Edge向けの技術検証です。実機タッチ、読み上げの更新通知、実OSのreduced-motion設定、基準端末での性能は未検証です。完成デザインや全ブラウザ対応として扱わないでください。
