"""Portable collections of explicit scenes; never reads browser state."""
from pathlib import Path
import re
from .scene import validate_scene
from .json_data import load_bounded_json

MAX_COLLECTION_BYTES = 64 * 1024
MAX_SCENES = 12


def validate_collection(data):
    if not isinstance(data, dict) or set(data) != {'version', 'title', 'scenes'}:
        raise ValueError('シーン集はversion・title・scenesを指定してください')
    if type(data['version']) is not int or data['version'] != 1:
        raise ValueError('シーン集のversionは1です')
    title = validate_scene(dict(version=1, model='rose', title=data['title']))['title']
    scenes = data['scenes']
    if not isinstance(scenes, list) or not 1 <= len(scenes) <= MAX_SCENES:
        raise ValueError('シーン集は1〜12件です')
    result, seen = [], set()
    for entry in scenes:
        if not isinstance(entry, dict) or set(entry) != {'id', 'scene'}:
            raise ValueError('各シーンはid・sceneを指定してください')
        identifier = entry['id']
        if not isinstance(identifier, str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,47}', identifier) or identifier in seen:
            raise ValueError('シーンidは重複しない英小文字・数字・ハイフン48文字以内です')
        seen.add(identifier)
        result.append(dict(id=identifier, scene=validate_scene(entry['scene'])))
    return dict(version=1, title=title, scenes=result)


def load_collection(path):
    return validate_collection(load_bounded_json(path, MAX_COLLECTION_BYTES))
