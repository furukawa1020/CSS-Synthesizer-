# Issue #114 — 座標観測manifestの一括照合

## 要件と変更

`python3 -m tools.coordinates --batch qa/evidence/.../index.json`で明示した観測を一括照合する。manifestは`{"snapshots":["model-fermat.json", "another.json"]}`の形式。JSONを自動分類して無視せず、指定した全ファイルを同じ独立座標checkerへ通す。結果は各ファイルの状態、合計点数・最大誤差を含み、1件でも失敗したら終了値1。単一snapshotの従来CLIも使える。

名前は同じディレクトリ内の通常JSONファイルのみ。重複・絶対パス・区切り・自分自身・symlinkを拒否する。件数256、manifest 64KiB、各snapshot 2MiB、snapshot合計16MiBの上限。strict JSONで重複キーや非有限数も拒否する。読み込みと検査だけを行い、ファイルやmtimeを変更しない。

## 検証

保存済みブラウザ座標を使い、合算、1件の座標不一致でも後続の観測を検査すること、単一/一括CLIの終了値、名前・件数・サイズ・symlink等の拒否、ファイルの非変更を確認。数式の正しさや全入力の網羅をmanifestの整合だけで保証しない。
