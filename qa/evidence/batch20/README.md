# 20件バッチのブラウザ観測

2026-10-28（日本時間）、Chrome155 / Linux UA / DPR1。点データは各192点の中心・入力・時計・描画領域を保持する。model-*.json、point-*.json、mirror-xy.json、focus-*.json、preset-*.json、print.jsonはtools.coordinatesへ直接渡せる。その他は表示状態のmetadata。

数式は全5モデルの実ブラウザ観測で独立照合した。集中表示・印刷は非既定値5.00/0°/90%で確認。幅と文字200%はiframe/CSS fixtureで、実機・実OS・実ブラウザUIズーム・実際の印刷の試験ではない。

初回の数式・表示観測は統合ソース8468e7dの作品で行った。最終のmodel-rose-final.json、desktop.jpg、text200.jsonは、初期モデルfallbackと拡大時の説明ボタン配置を修正した0d95063の作品で採取した。mobile.jpgは初回の360px幅・文字100%での説明配置。最終状態と検証範囲はdocs/batch20/validation.mdへ記録する。

上記の短いSHAはローカル検証スナップショットの識別子であり、公開GitHub commitを示すものではない。数理式とengine.cssは採取後に変更していない。最終の配布生成元はZIPのmanifestに記録する。
