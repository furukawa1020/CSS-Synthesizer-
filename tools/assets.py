"""One current, source-specific distribution definition; no import-time registry read."""
from pathlib import Path
from .models import load_models
from .presets import load_presets

SOURCE = Path(__file__).resolve().parents[1] / 'src'


def asset_specs(source=SOURCE):
    source = Path(source)
    models = load_models(source)
    presets = load_presets(source, {model['id'] for model in models})
    return (
        ('index.html', 192), ('samples-96.html', 96), ('samples-384.html', 384),
        ('style.css', None), ('engine.css', None),
        *((preset['file'], 192) for preset in presets),
        ('gallery.html', 96 * len(presets)),
        ('compare.html', 96 * len(models)),
    )
