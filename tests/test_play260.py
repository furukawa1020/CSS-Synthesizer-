"""Check real starter data and usable native fragment targets."""
from html.parser import HTMLParser
import math
import unittest
from tools.build import ROOT, single_html
from tools.models import load_models
from tools.presets import load_presets
from tools.source import expand_fragments
from tools.scene import render_scene, standalone_html
from tools.starters import starter_links, starter_points


class Links(HTMLParser):
    def __init__(self):super().__init__();self.ids=set();self.hrefs=[];self.times=[]
    def handle_starttag(self,tag,pairs):
        a=dict(pairs)
        if 'id' in a:self.ids.add(a['id'])
        if tag=='a':self.hrefs.append(a.get('href',''))
        if tag=='input' and a.get('name')=='time':self.times.append(a['id'])


class PlayTests(unittest.TestCase):
    def test_starters_derive_from_available_registry_and_link_real_pages(self):
        presets=load_presets(ROOT/'src');p=Links();p.feed(starter_links(presets))
        self.assertEqual(len(p.hrefs),4)
        self.assertTrue(set(p.hrefs)<={x['file'] for x in presets})
        small=Links();small.feed(starter_links(presets[:1]))
        self.assertEqual(small.hrefs,['preset-circle.html'])

    def test_circle_preview_has_equal_coordinate_scales(self):
        circle=load_presets(ROOT/'src')[0]
        points=starter_points(circle)
        self.assertEqual(len(points),48)
        for x,y in points:self.assertAlmostEqual(math.hypot(x-50,y-50),.7*44)

    def test_primary_fragment_links_target_existing_ticks_and_time_is_unique(self):
        p=Links();p.feed(render_scene(dict(version=1,model='rose',count=96)))
        for href in p.hrefs:
            if href.startswith('#'):self.assertIn(href[1:],p.ids)
        self.assertEqual(sorted(p.times),['time-auto','time-play','time-stop'])

    def test_standalone_keeps_play_controls_without_missing_starter_pages(self):
        html=standalone_html(render_scene(dict(version=1,model='rose',count=96)))
        self.assertNotIn('class="play-start"',html)
        self.assertIn('class="play-transport"',html)
        p=Links();p.feed(html)
        for href in p.hrefs:self.assertTrue(href.startswith(('#','https://')))

    def test_home_starts_still_with_a_reachable_trial_before_examples(self):
        source = ROOT / 'src'
        template = expand_fragments((source / 'page.html').read_text(), source)
        models = load_models(source)
        presets = load_presets(source)
        html = single_html(template, models, presets, 192, home=True)
        self.assertIn('--k-raw:2;--phase-raw:90;--amplitude-raw:0.7', html)
        self.assertIn('name="time" value="stop" checked', html)
        trial = html.split('class="first-try continuous-controls"', 1)[1].split('class="play-transport"', 1)[0]
        self.assertLess(html.index('class="stage"'), html.index('class="first-try'))
        self.assertLess(html.index('class="play-start"'), html.index('class="stage"'))
        parser = Links()
        parser.feed(html)
        self.assertIn('href="#tick-phase-0"', trial)
        self.assertIn('href="#tick-phase-1"', trial)
        for target in ('tick-phase-0', 'tick-phase-1', 'tick-k-1'):
            self.assertIn(target, parser.ids)
        self.assertNotIn('class="first-try', single_html(template, models, presets, 192, presets[0]))
