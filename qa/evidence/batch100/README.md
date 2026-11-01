# 12モデルと点の表示の観測

2026-11-01（日本時間）。Chrome155 / Linux UAで採取した45ケース・5,857点の座標と接線状態。DOMの点中心と観測した入力・時計を独立数式へ通す。--x/--yから期待値を作っていない。

index.json / tangents-index.jsonは明示一覧。shared-1〜3.jsonは12モデルずつの共有条件。counts.jsonは最終の対象点数方式の27組合せ、gallery/layoutは一覧と幅。

checks.jsonのstatesは座標採取時のmask状態を含み、旧方式のcounterReset/Increment/Contentも残している。この時点のcounter集計は画面で0になったため撤去した。最終のlabelの集計は型付きattrとCSS算術へ変更し、counts.jsonと最終画像で確認した。座標式とmaskは同じで、ラベル変更は点の座標を変えない。

静的な時計端点、印刷CSS、iframeは実動画の周期境界・実印刷・実機ではない。[条件と制限](../../../docs/batch100/validation.md)。配布ZIPには含めない。
