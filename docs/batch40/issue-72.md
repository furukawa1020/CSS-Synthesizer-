# Issue #72 — JSON定義の曖昧な値を拒否する

モデルとプリセットのJSONで、同じオブジェクトのキーを後勝ちで解釈しない。共通の`tools.json_data`を通し、重複キー、`NaN`、`Infinity`、`-Infinity`、浮動小数点の有限範囲を超える指数表記を生成前に拒否する。通常の文字列・配列・数値・真偽値・nullは保持する。

`python3 -m unittest discover -s tests -p 'test_json_data.py' -v`で通常値、入れ子の重複、非有限数、両レジストリへの適用、不正な定義による生成失敗時の既存build保持を確認した。これはプロジェクトの定義ファイル用の読み込み規則であり、一般的なJSON Schema検証ではない。
