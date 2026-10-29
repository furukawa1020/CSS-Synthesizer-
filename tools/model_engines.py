"""Check this project's declared model bindings, not the correctness of equations."""
import re

from .coordinates import SUPPORTED_MODELS
from .models import validate_models

# Lissajous is the .sample base equation, so it needs no checked-model override.
DEFAULT_MODELS = frozenset({'lissajous'})
_BINDING = re.compile(r'\.lab:has\(#model-([a-z][a-z0-9-]*):checked\)')
_LEAF_RULE = re.compile(r'([^{}]+)\{([^{}]*)\}')
_X_DECLARATION = re.compile(r'(?:^|;)\s*--x\s*:')
_Y_DECLARATION = re.compile(r'(?:^|;)\s*--y\s*:')
_IGNORED = re.compile(r'''/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*' ''', re.VERBOSE)


def validate_engine_models(models, engine_css, supported_models=SUPPORTED_MODELS):
    """Require coordinate-block model bindings and independent-checker IDs.

    Ignore comments and quoted content. This recognizes the author's current
    selector convention rather than parsing arbitrary CSS or proving its math.
    Validation runs before static-view aliases are generated.
    """
    validate_models(models)
    identifiers = {model['id'] for model in models}
    if not DEFAULT_MODELS <= identifiers:
        raise ValueError('既定描画のlissajousモデル定義がありません')
    if identifiers != set(supported_models):
        missing = identifiers - set(supported_models)
        extra = set(supported_models) - identifiers
        raise ValueError('モデル定義と独立checkerの対応が一致しません: '
                         + ', '.join(sorted(missing | extra)))
    source = _IGNORED.sub('', engine_css)
    bindings = set()
    aliases = set()
    default_coordinates = False
    for prelude, body in _LEAF_RULE.findall(source):
        selected = set(_BINDING.findall(prelude))
        aliases.update(selected)
        # Tangent/paint blocks may use the same model selector. They are not
        # render bindings unless both coordinate declarations are in this block.
        if _X_DECLARATION.search(body) and _Y_DECLARATION.search(body):
            bindings.update(selected)
            if prelude.strip() == '.sample':
                default_coordinates = True
    if not default_coordinates:
        raise ValueError('既定描画の.sampleに両座標宣言がありません')
    missing = identifiers - DEFAULT_MODELS - bindings
    extra = aliases - identifiers
    if missing or extra:
        raise ValueError('モデル定義とCSS描画selectorの対応が一致しません: '
                         + ', '.join(sorted(missing | extra)))
    return {'models': sorted(identifiers), 'bindings': sorted(bindings),
            'default_models': sorted(DEFAULT_MODELS)}
