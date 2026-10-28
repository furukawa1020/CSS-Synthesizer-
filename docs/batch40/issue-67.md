# Issue #67 — ネイティブな開閉のトランジション

## 要件と変更

Dialog・表示設定Popover・入力説明Popoverの開閉を120msの透明度変化でつなぐ。`@starting-style`で非表示からの開始値を与え、`display`と`overlay`の`allow-discrete`で閉じる間もトップレイヤーを維持する。位置・transformをアニメーションさせず、入力説明のimplicit anchorに干渉しない。

`transition-behavior`・`overlay`・`:popover-open`の対応をまとめて検出する。非対応では既存の即時開閉を使う。端末の`prefers-reduced-motion: reduce`ではtransitionを解除する。DialogのInvoker CommandsやPopoverのネイティブな閉じ方を変更しない。

## 検査

`python3 -m tools.build`と`python3 -m tools.audit`が成功。実ブラウザでの開閉・Escape・フォーカス復帰・画面内配置は統合検証に記録する。OS設定による動き軽減と未対応ブラウザでの実観測は未検証。

一次資料：[Chromeの開閉アニメーション解説](https://developer.chrome.com/blog/entry-exit-animations)。
