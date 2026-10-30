# 静的配布物と検査

Python標準ライブラリでZIPとSHA-256のmanifestをローカルに生成する。公開・デプロイ・GitHub Releaseの発行は行わない。作品の動作確認の範囲は[今回の検証](batch60/validation.md)と[受け入れ状況](acceptance.md)を参照する。

## 生成する

Python 3.11以上とGitを使う。追加パッケージのインストールは不要。

```sh
python3 -m tools.source_audit
python3 -m tools.build
python3 -m tools.build --check
python3 -m unittest discover -s tests -v
python3 -m tools.audit
python3 -m tools.package
```

`tools.package`は未コミット変更がないことを確認し、現在のソースを必ず再ビルドしてから監査・配布生成へ進む。正常な再生成では古いQA fixtureを除去する。生成や候補監査に失敗した場合は前回の`build/`を残す。配置は二段階のrenameであり、電源断や並行HTTPリクエストに対する完全な原子性は保証しない。

出力は`dist/css-synthesizer-v0.1.zip`と`dist/css-synthesizer-v0.1.manifest.json`。ZIPを展開してHTMLとCSSを同じディレクトリに置き、現行Chrome / Edgeで`index.html`を開く。Pythonはブラウザ内の実行には不要。

## 同梱する21ファイル

| ファイル | 役割 |
| --- | --- |
| `index.html` | 192点の作品・8モデル・操作画面 |
| `samples-96.html`・`samples-384.html` | 点数の比較用ページ |
| `preset-circle.html` | 反復2.00・位相90°・振幅70%のリサージュ |
| `preset-weave.html` | 反復5.00・位相0°・振幅90%のリサージュ |
| `preset-two-waves.html` | 反復2.00・位相180°・振幅60%の波形 |
| `preset-fine-wave.html` | 反復7.00・位相90°・振幅40%の波形 |
| `preset-rose.html` | 反復5.00・位相0°・振幅85%の花弁 |
| `preset-spiral.html` | 反復4.00・位相90°・振幅90%の渦巻き |
| `preset-orbit.html` | 反復3.00・位相180°・振幅85%の合成軌道 |
| `preset-fermat.html` | 反復4.00・位相0°・振幅90%のフェルマー渦巻き |
| `preset-damped-wave.html` | 反復4.00・位相90°・振幅90%の減衰波 |
| `preset-standing-wave.html` | 反復2.00・位相0°・振幅85%の定在波 |
| `compare.html`・`compare-192.html` | 各96/192点・同じ入力と時計で複数モデルを比較 |
| `features.html` | 18のCSS条件の構文診断と要手動確認の説明 |
| `gallery.html` | 10プリセットを各96点・時計0で比較する静的一覧 |
| `style.css` | 分割した画面用CSSを合成したもの |
| `engine.css` | 入力・時計・全モデルの描画用CSSを合成したもの |
| `README.txt` | 展開後の使い方と制限の参照先 |
| `SHA256SUMS` | 上記19のHTML/CSSのSHA-256一覧 |

10プリセットは各192点で、指定値・時間停止・時計0から始まる別ページ。ギャラリーでは同じ初期値を各96点で比較できる。編集状態を保存したファイルではない。点数ページやプリセット間を移動する際、現在の値や時間の保持は保証しない。

`tools.assets`がソースのモデル・プリセット定義から配布対象を決め、生成・監査・配布・ZIP検査で共有する。現在の対象は17 HTML・2 CSSの19アプリファイル。`package_release()`はこのファイル定義を再監査する。余分なファイル・不足・ディレクトリ・シンボリックリンクは拒否する。開発ソース、検証資料、Git情報はZIPへ入れない。

## 展開せずに検査する

```sh
python3 -m tools.verify dist/css-synthesizer-v0.1.zip
python3 -m tools.verify dist/css-synthesizer-v0.1.zip --manifest dist/css-synthesizer-v0.1.manifest.json
```

成功時のJSONは`ok: true`、終了コードは0。失敗時は`ok: false`と理由を返し、終了コードは1となる。検査中にZIPのファイルをディスクへ展開しない。

検査する内容は、配布定義と一致するファイル名・数、重複、通常ファイル性、パス逸脱、暗号化、無圧縮形式、サイズ上限、内部SHA-256、HTML/CSSの禁止内容、ネイティブ操作と同梱ページ間の参照先。内部のハッシュ一覧を作り直しても、スクリプトや壊れた操作参照は静的監査で拒否する。

この検査器は本プロジェクトの無圧縮ZIP形式専用で、一般のZIP検査器ではない。上限はZIP全体16MiB、各メンバー2MiB、総展開サイズ8MiB。ZIP全体の上限はファイル読み取り前にも確認し、各メンバーのサイズ・形式はメンバーデータの読み取り前に検査する。

CIも配布生成直後のZIPを外部manifest付きで検査する。外部manifestを指定した場合は、ZIP全体のSHA-256に加え、version・archive・sourceRevisionの形式、全メンバーの名前・バイト数・SHA-256・重複も照合する。すべてが一致したときだけmanifest_verifiedがtrueになる。生成元SHAの形式検査は、そのcommitの作者や公開元の認証ではない。指定しない場合、同梱の`SHA256SUMS`によるアプリファイルの整合性を調べるだけで、READMEやZIP全体の改変を保証して検出するものではない。manifestも含めて置き換えられた場合の発行者の真正性は、これらのハッシュだけでは証明できない。

## 再現性と生成元

ZIPはファイル順・時刻・属性を固定したZIP STORE形式。同じHTML/CSSなら、元ファイルの更新時刻や生成元commitが違ってもZIPのバイト列は同じになる。

完全な生成元commit SHAはZIPの外のmanifestへ記録する。manifestはZIP全体と全同梱ファイルのSHA-256を持ち、生成日時は含めない。CLIは未コミット変更を拒否し、その時点の`HEAD`から再生成した内容を使う。

配布検査は実ブラウザの操作、実機タッチ、読み上げ、描画性能、file://での直接表示、実際の印刷の検証を置き換えない。未確認の環境は[Issue #3](https://github.com/furukawa1020/CSS-Synthesizer-/issues/3)へ残す。


## 保存した観測を一括で照合する

```sh
python3 -m tools.coordinates --batch qa/evidence/batch60/index.json
```

manifestが列挙した、同じディレクトリの観測JSONを順に検査する。各結果・合計点数・最大誤差を返し、1件でも失敗すると終了コードは非ゼロ。欠落や不正な参照も成功として省略しない。これは過去の有限ケースの回帰検査であり、ブラウザを起動し直す検査、実機性能、全入力の証明ではない。接線の観測はtools.tangentsで別に検査する。

モデル定義とCSS選択子・独立checkerの対応も生成候補で検査する。基底のリサージュは明示した例外とし、未実装の名前だけが選択肢に追加されることを防ぐ。この対応検査自体はCSSの数式の正しさを証明しない。

## 比較表示と時計の検査

今回の配布構成も17 HTML・2 CSS、使い方とハッシュ一覧込み21エントリー。`--require-all`を座標の単一/一括CLIに指定すると全count点を要求する。接線は`python3 -m tools.tangents --batch qa/evidence/batch80/tangents-index.json`で一括照合できる。座標と接線の最大誤差はCSS px/度を分ける。観測資料とQA fixtureはZIPに入れない。
