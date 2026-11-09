"""Native discrete controls share the existing labels, readouts, and engine."""
CHOICES = {
    'phase': ('°', (0, 45, 90, 180, 270)),
    'k': ('', (1, 2, 3, 4, 6, 8)),
    'amplitude': ('%', (25, 50, 70, 100)),
}


def quick_controls(state, selected=None):
    if selected is None:
        return '<form id="quick-values" class="quick-values-form" aria-label="開始値へ戻す"><button type="reset" class="quick-reset">数値を戻す</button></form>'
    if selected not in CHOICES:
        return ''
    key = selected
    unit, values = CHOICES[key]
    initial = state[key]
    choices = [(f'quick-{key}-initial', initial, True)]
    choices.extend((f'quick-{key}-{value}', value, False) for value in values if value != initial)
    choices.sort(key=lambda choice: choice[1])
    options = []
    for identifier, value, is_initial in choices:
        label = f'{value:.2f}' if key == 'k' else f'{value:g}'
        options.append(
            f'<option id="{identifier}" value="{value:g}"'
            + (' selected' if is_initial else '')
            + f'>{label}{unit}</option>'
        )
    return (
        f'<div class="quick-choices"><select id="quick-{key}-control" name="quick-{key}"'
        f' form="quick-values" aria-labelledby="{key}-label" aria-describedby="{key}-help">'
        + ''.join(options) + '</select></div>'
    )


def input_modes():
    return (
        '<fieldset class="input-modes" aria-describedby="quick-help"><legend>値の変え方</legend><div class="choices">'
        '<label><input id="input-basic" type="radio" name="input-mode" value="basic" checked>'
        '<span>数値を選ぶ</span></label>'
        '<label><input id="input-scroll" type="radio" name="input-mode" value="scroll">'
        '<span>帯で細かく</span></label></div><p id="quick-help" class="quick-help">選択欄で値を変えます。帯へ切り替えると、連続値を調整できます。</p><p class="mode-note">方式ごとに値を保持します。この欄を閉じても、帯での調整を続けられます。</p></fieldset>'
    )
