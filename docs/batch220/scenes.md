# 保存シーンとシーン集

これは明示した初期状態を持ち運ぶ機能です。ブラウザー内の現在値は読み取りません。

```sh
python3 -m tools.scene qa/scene-example.json --check --json
python3 -m tools.scene qa/scene-example.json --canonical
python3 -m tools.scene --list-models
python3 -m tools.scene --list-view
python3 -m tools.scene qa/scene-example.json --output tmp/my-scene --json
```

親フォルダーtmpを先に作り、出力先は存在しない名前を指定します。入力検査と正規JSON出力はファイルを作りません。viewは一覧のキーと選択ID（チェックボックスは真偽値）を指定します。対応構文と実際のブラウザー動作は別です。

シーン集はversion:1、title、scenesのオブジェクトです。scenesは1〜12件、各項目は一意のidと単一シーン形式のsceneです。idは英小文字で始まり、英小文字・数字・ハイフン48文字以内です。

```sh
python3 -m tools.scene_collection qa/scene-collection-example.json --check
python3 -m tools.scene_collection qa/scene-collection-example.json --output tmp/my-collection
python3 -m tools.scene_collection tmp/my-collection --verify
```

生成したindex.htmlを開きます。各子フォルダーは単独でも開けるHTML/CSS・scene.jsonを含みます。collection.jsonは全初期状態、checksums.jsonは全内容のSHA-256です。検査は改変・欠落・追加項目・不正なリンク先形式を検出し、発行者の署名やブラウザー動作は保証しません。上限はmanifest64KiB、検査対象1ファイル2MiB、合計32MiBです。既存出力は置き換えず、通常の書き込み失敗では今回作った出力を片付けます。電源断時の原子性は保証しません。
