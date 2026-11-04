"""Behavior contracts for the revised native-disclosure workspace."""
from html.parser import HTMLParser
import unittest
from tools.scene import render_scene, validate_scene


class Structure(HTMLParser):
    def __init__(self):
        super().__init__(); self.details=[]; self.inputs={}; self.bands=[]
    def handle_starttag(self, tag, pairs):
        attrs=dict(pairs)
        if tag=='details': self.details.append('open' in attrs)
        if tag=='input': self.inputs[attrs.get('id')]=attrs
        if 'input-band' in attrs.get('class','').split(): self.bands.append(tuple(self.details))
    def handle_endtag(self,tag):
        if tag=='details': self.details.pop()


class WorkspaceTests(unittest.TestCase):
    def test_timeline_sources_remain_outside_collapsed_disclosures(self):
        parser=Structure();parser.feed(render_scene(dict(version=1,model='ellipse')))
        self.assertEqual(len(parser.bands),3)
        self.assertEqual(parser.bands,[(),(),()])
        self.assertEqual(sum(a.get('name')=='model' for a in parser.inputs.values()),16)

    def test_saved_scene_selections_survive_model_disclosure(self):
        scene=validate_scene(dict(version=1,model='rose',k=2.37,phase=17,amplitude=73,view={'point-shape':'shape-ring','mirror-x':True},clock_period_seconds=48,clock_direction='reverse'))
        parser=Structure();parser.feed(render_scene(scene))
        for identifier in ('model-rose','shape-ring','mirror-x','period-48','direction-reverse','time-stop'):
            self.assertIn('checked',parser.inputs[identifier])
        self.assertNotIn('checked',parser.inputs['model-lissajous'])
