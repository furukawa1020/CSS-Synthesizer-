"""Native discrete controls share the existing labels, readouts, and engine."""
GROUPS = (
    ('phase', '@@MODEL_PHASE_HELP@@', '位相', '°', (0, 45, 90, 180, 270)),
    ('k', '@@MODEL_K_HELP@@', '@@MODEL_K_LABELS@@', '', (1, 2, 3, 4, 6, 8)),
    ('amplitude', '@@MODEL_AMPLITUDE_HELP@@', '@@MODEL_AMPLITUDE_LABELS@@', '%', (25, 50, 70, 100)),
)


def quick_controls(state, selected=None):
    if selected is None:
        return '<form id="quick-values" class="quick-values-form" aria-label="開始値へ戻す"><button type="reset" class="quick-reset">3つの数値を戻す</button></form>'
    group = next((group for group in GROUPS if group[0] == selected), None)
    if group is None:
        return ''
    key, hint, title, unit, values = group
    initial = state[key]
    choices = [(f'quick-{key}-initial', initial, True)]
    choices.extend((f'quick-{key}-{value}', value, False) for value in values if value != initial)
    choices.sort(key=lambda choice: choice[1])
    labels = []
    for identifier, value, checked in choices:
        number = f'{value:g}'
        labels.append(
            f'<label><input id="{identifier}" type="radio" form="quick-values" name="quick-{key}" value="{number}"'
            + (' checked' if checked else '')
            + f'><span>{number}{unit}</span></label>'
        )
    return f'<div class="quick-choices" role="group" aria-labelledby="{key}-label" aria-describedby="{key}-help">' + ''.join(labels) + '</div>'


def input_modes():
    return (
        '<fieldset class="input-modes"><legend>値の変え方</legend><div class="choices">'
        '<label><input id="input-basic" type="radio" name="input-mode" value="basic" checked>'
        '<span>数値を選ぶ</span></label>'
        '<label><input id="input-scroll" type="radio" name="input-mode" value="scroll">'
        '<span>帯で細かく</span></label></div><p class="mode-note">方式を切り替えると、それぞれで最後に使った値に戻ります。</p></fieldset>'
    )
