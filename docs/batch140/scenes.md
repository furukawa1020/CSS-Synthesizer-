# JSONから保存シーンを生成する

ブラウザーの操作状態を読み取る機能ではありません。利用者がJSONへ記入した初期状態を、PythonでHTML/CSSへコンパイルします。ブラウザー内の調整は自動保存しません。既存の要件で保留しているブラウザー永続保存とは区別します。

```sh
mkdir -p tmp
python3 -m tools.scene qa/scene-example.json --output tmp/my-scene
python3 -m tools.serve --directory tmp/my-scene --port 0 --quiet
```

表示されたlocalhost URLを開きます。出力はindex.html、style.css、engine.css、scene.jsonの4ファイルです。実行にはPythonも不要ですが、file://での動作確認は未完了です。フォルダーを移動するときは4ファイルを一緒に持ち運びます。出力先が存在する場合は中身にかかわらず拒否し、上書きしません。生成・監査後に新規ディレクトリを予約してファイルを配置します。配置中の完全な原子性や電源断耐性は保証しません。

出力したscene.jsonを別の出力先へ渡すと、同じソース版ではHTML/CSS/JSONがバイト単位で一致します。ブラウザーや画面幅によるスクロール初期位置・丸め・数値精度の完全一致を保証する意味ではありません。今回、新しい保存シーンの実ブラウザー確認は接続制限のため未完了です。

## 形式

version=1とmodelが必須です。未指定の値はk=3、phase=90、amplitude=80、count=192、clock_radians=0、title=保存シーン、view={}、processingは無加工です。modelはsrc/models.jsonの12種から選びます。

- k：1〜8、0.01刻み。
- phase：0〜360、1度刻み。
- amplitude：25〜100、1%刻み。
- count：96/192/384。
- clock_radians：0〜2πの有限数。位相phaseとは別で、停止から始まります。再生すると保存した時計位置から進みます。時計の周期・方向切替では従来どおり位置が移り得ます。
- title：1〜120文字の1行テキスト。HTMLとして解釈せず、題名として表示します。
- view：既存の表示設定のラジオグループ名→選択ID、チェックボックスID→真偽値。例は同梱JSONを参照。比較専用設定・時間・モデルを混入できません。表示設定resetは、この保存シーンで指定したHTMLの初期選択へ戻します。
- processing：交換swap、折返しfold、投影projection、gain_x/y、offset_x/y、quantum、bound。[既存加工の定義](../batch120/processing.md)を使います。処理中の接線は従来どおり丸点になります。

JSONは16KiBまで。未知キー・重複キー・非有限数・入力精度の不一致・未対応設定を拒否します。scene.json自体はプレビューのHTTP配信対象ではなく、フォルダー内のローカルファイルとして再利用します。正規化JSONは版・省略値・キー順・UTF-8を固定し、ソース版をまたぐ生成一致は保証しません。

単独出力には一覧・比較・点数切替の別ページを含めず、そのページへのリンクを除きます。モデル・入力・停止/再生・表示設定は引き続きその画面で操作できます。

## 開発検証

```sh
python3 -m tools.build
python3 -m tools.validate
python3 -m tools.validate --json
python3 -m unittest discover -s tests -v
```

validateはソース監査・ビルド鮮度・HTML/CSS参照監査・qa/evidence/batch*/配下の座標、接線、共有条件manifestを検査します。ソースとbuildは書き換えず、一時生成した候補との比較を行います。観測manifestが0件のときは失敗します。ユニットテストや配布ZIP作成を代行するコマンドではありません。

プレビューは127.0.0.1だけへbindし、localhost/127.0.0.1/::1のHostだけを受理します（IPv6でのlistenは行いません）。ポートをHostへ指定する場合は実際のポートと一致させます。リバースプロキシ・公開用サーバーとしては使いません。直下の通常HTML/CSS以外、入れ子パス・シンボリックリンク・絶対URLは拒否します。エラー応答にもCSP・nosniff・no-storeを付けます。
