# Issue #34：HTMLネイティブ操作と参照先の監査

実装前の範囲：HTMLのparse後に重複IDと同一ページのID参照を照合し、前方参照を認める。`popovertarget`はpopover要素、Dialog命令の`commandfor`はdialog要素、Popover命令はpopover要素を要求する。JSイベントに依存する`--custom`や未採用命令はこのJSゼロ作品のガードとして拒否する。

label/output、ARIAのID参照、ローカルfragmentリンクも検査する。`#`・`#top`のページ先頭移動と、外部の説明用リンクを未解決ID扱いしない。同梱ファイル間の参照はディレクトリ監査で照合し、ZIP検査でも展開せず同じ照合を使う。

プロジェクト固有の操作規則：`commandfor`または`popovertarget`を持つbuttonには`type="button"`を明示する。フォームのsubmit/reset動作を先に実行する構成を配布しないための制限であり、一般のHTML全体を不正と定義するものではない。大文字小文字の異なる`type="BUTTON"`も同じ指定として扱う。

検証予定：前方参照・正しいDialog/Popover・ARIA/label、重複ID、欠落、対象型不一致、URLエンコードしたfragment、別ページと欠落ファイルを確認する。これは動作の構造検査であり、ブラウザAPI対応や読み上げの実測ではない。

検証結果：正しい前方参照、Dialog/Popoverの対象型、ARIA/label、URLデコード、同梱ページ間参照など8件の監査テストと、内部hash更新後も破損したページ間リンクをZIP検査が拒否する回帰検査を確認した。Popover actionは大文字小文字を区別せず、ボタン型以外のinputを呼出し元として通さない。未展開・空の断片マーカーも拒否する。

追試：フォーム内のsubmit/reset/button型省略を、commandforとpopovertargetのそれぞれで拒否し、明示したbutton型を受理する回帰検査を追加した。
