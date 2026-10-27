# Issue #28：操作ガイドをHTML Dialogで開く

2026-10-28（日本時間）。主操作を読み返したいとき、ヘッダーのボタンから短いガイドをモーダルで参照する。

`commandfor`と`show-modal`で開き、Dialog内の`request-close`とEscapeで閉じる。全ボタンにtype=buttonを明示する。Dialogはネイティブのモーダル・フォーカス管理に任せる。開閉でモデル・値・再生ラジオは変更しない。従来のdetails説明とリンクも維持する。

対象は既存のChrome155検証環境。CSSの`:open`対応をInvoker Commands対応の証拠にしない。他ブラウザへの同等動作は保証しない。ビルド・監査を行い、開閉・Escape・フォーカス復帰の実ブラウザ観測は統合後に記録する。

一次資料：https://developer.chrome.com/blog/command-and-commandfor 、https://developer.chrome.com/blog/chrome-139-beta （request-close）。
