"""One current, source-specific distribution definition; no import-time registry read."""
from pathlib import Path
from .models import load_models
from .presets import load_presets
from .gallery import GALLERY_COUNTS, gallery_filename
from .comparison import COMPARISON_COUNTS, comparison_filename

from .synth import PATCHES, SAMPLE_COUNT

SOURCE = Path(__file__).resolve().parents[1] / 'src'


def asset_specs(source=SOURCE):
    source = Path(source)
    models = load_models(source)
    presets = load_presets(source, {model['id'] for model in models})
    return (
        *((name, SAMPLE_COUNT) for name in PATCHES),
        ('samples-96.html', 96), ('samples-192.html', 192), ('samples-384.html', 384),
        ('style.css', None), ('engine.css', None),
        *((preset['file'], 192) for preset in presets),
        *((gallery_filename(count), count * len(presets)) for count in GALLERY_COUNTS),
        *((comparison_filename(count), count * len(models)) for count in COMPARISON_COUNTS),
        ('features.html', 0),
    )
