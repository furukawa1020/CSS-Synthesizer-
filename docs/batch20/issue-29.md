# Issue #29：入力説明をその場で開く

2026-10-28（日本時間）。各入力の範囲と数式上の意味を、調整している場所で読み返せるようにする。

反復・位相・振幅ごとにpopover=autoの説明を一つ置き、popovertargetのボタンで開く。通常の文書として構成し、menuロールは付けない。閉じるボタン・Escape・外側クリックを使う。CSS Anchor Positioningがある場合は呼び出しボタンを暗黙アンカーとして配置し、上下左右の反転を試す。Anchor非対応時は中央、Popover自体が非対応のときは説明を通常フローへ表示する。

説明は複数モデルに共通する定義を述べる。反復を再生速度と呼ばない。位相・振幅の作用がモデルで異なることを隠さない。説明を見ても入力や時計を変更しない。

ビルド・監査・参照先の静的確認を行った。実ブラウザの位置・閉じる・Escape・狭幅は統合後の確認対象。

一次資料：https://html.spec.whatwg.org/multipage/popover.html 、https://drafts.csswg.org/css-anchor-position/ 。
