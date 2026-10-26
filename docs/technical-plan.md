# 技術検証計画と根拠

## 1. 技術の採用基準

新しいという理由だけでは採用しない。「どの体験に必要か」「CSSだけで成立するか」「非対応時にどうなるか」を確認する。次の表は資料調査に基づく候補であり、本リポジトリで動作確認済みという意味ではない。

| 機能 | 用途候補 | 根拠 | 初期方針 |
| --- | --- | --- | --- |
| sibling-index/count | サンプルの位置を順番と個数から導く | https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/sibling-index | 採用候補。CSSがDOMを増やす機能とは説明しない |
| @property | 時間位相・入力値の型と補間 | https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@property | 採用候補。値の継承範囲を制限する |
| sin/cos | 各モデルの座標計算 | https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/sin | 描画に必要 |
| scroll-timeline / timeline-scope | スクロール入力を値へ写す | https://developer.chrome.com/docs/css-ui/scroll-driven-animations | 最大の不確実性。最初に検証 |
| ::scroll-button / scroll-marker | 操作可能な目盛りと移動 | https://developer.chrome.com/blog/carousels-with-css | キーボードとタッチの到達性を確認 |
| :has | ネイティブフォームの状態を描画へ反映 | https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/:has | 採用候補。広い範囲の毎フレーム再評価を避ける |
| @function | 正規化や座標計算の共通化 | https://developer.chrome.com/blog/new-in-chrome-139 | 有用な重複を解消するときのみ採用。sinのラッパーだけなら不要 |
| typed arithmetic / round | 型変換と表示精度 | https://developer.chrome.com/release-notes/140 | 対応・丸め・単位を先に確認 |
| commandfor / dialog | 解説の開閉 | https://developer.chrome.com/blog/command-and-commandfor | 基本の組み込み操作のみ使用候補 |

random、border-shape、corner-shape、Grid Lanes、interestforは今回の主目的に必須ではない。数を増やすための導入はしない。

## 2. スパイク

すべて、最終UIと分けた最小ページで確認する。まだ作成・実行していない。

| ID | 検証する仮説 | 合格条件 | 失敗した場合 |
| --- | --- | --- | --- |
| S-01 | 子のスクロール位置を共有スコープで描画の値へ接続できる | 始端・中点・終端で値と形が期待どおり変わる。循環依存がない | radioの離散入力へ戻し、連続入力は保留 |
| S-02 | 表示値と計算値を同じ有効値から導ける | k/φ/Aが定義した精度で一致し、符号・単位・端点も正しい | 精度または入力方式を変更し、要件へ反映 |
| S-03 | 主要入力がマウス・キーボード・タッチで成立する | 両端まで到達し、フォーカス・読み上げ・値の確認ができる | 入力を置き換える。操作不能な外観で補わない |
| S-04 | 等方座標で2モデルを描ける | 横長・正方形・縦長で数学的な形を保つ | 固定比率の描画領域など代替を比較 |
| S-05 | 時間停止・再開・reduced motionをJSなしで両立できる | 停止中の編集、続きから再開、初期自動停止を区別できる | reduced motionでは手動静止作品に限定するなど方針を明記 |
| S-06 | 必要な密度で負荷を許容できる | 96/192/384点を同一条件で測り、必要な最小密度が目標を満たす | 点数・線の方式・動きの範囲を見直す |

## 3. 測定記録の書式

各検証は、日付、OS、ブラウザの完全なバージョン、画面サイズ、DPR、端末/CPU、電源状態、スパイクのcommit、入力方法、手順、期待値、実測値、画像、判定を記録する。

ブラウザの読み取り専用の検証スクリプトや開発ツールによる計測は、作品にJSを配信することと区別する。測定用コードが公開成果物へ混入しないよう検査する。

CSS.supportsの構文検出だけで挙動の合格にしない。CSSの対応、HTMLのコマンドの対応、アクセシビリティの挙動は別々に確認する。

## 4. 配布物の条件

- アプリのソースと生成HTMLにscript要素、イベントハンドラ属性、javascript: URLがない。
- Canvas/WebGL等へ描画を逃がさない。SVGで信号を描きながらCSS描画と称さない。
- スクリプトを禁止するCSP下で主要操作を確認する。
- 開発用のライブリロード、計測コード、外部依存が成果物に混入しない。
- ビルドが必要なら、未生成のテンプレートを配布せず再生成方法をREADMEに記す。

## 5. アーキテクチャの仮案

入力状態（ネイティブ要素）→有効値（型付きCSS値）→数理モデル（正規化座標）→描画（等方写像）の責務を分ける。作品の説明は同じモデル仕様から作る。

値の継承やstyle/layoutの無効化が広がる場合はスコープを小さくする。transformなら必ず高速、CSSなら必ずGPU描画、という前提は置かない。
