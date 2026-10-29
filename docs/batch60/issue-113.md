# Issue #113 — 外部manifest全記述のZIP照合

## 要件と変更

外部manifestのZIP全体hashだけを確認してmanifest_verifiedをtrueにしない。v0.1のversion・archive、40桁小文字hexのsourceRevision、全ファイル名・バイト数・SHA-256をZIPの実内容へ照合する。README.txtとSHA256SUMSも対象。重複名・欠落・不正な型・JSON重複キー・非有限数を拒否する。現在の形式を厳密に検査するため、未知の項目や別versionは受理しない。

ZIPファイル自体のローカル名が変更されても、manifestのarchiveは配布形式の正規名を検査する。sourceRevisionは形式を確認し、そのcommitの内容や発行者をネットワークで認証するものではない。

## 検証

正規のpackage_release出力を受理し、header・各メンバーの記述・README・SHA256SUMSの改変と異常JSONを拒否する単体検査を追加。展開せず検査する既存方針は維持。SHA-256の整合性を署名・発行者認証とは扱わない。
