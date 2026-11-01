import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from tools.coordinates import inspect_snapshot
from tools.shared_conditions import inspect_shared_batch, main

class SharedConditionsTests(unittest.TestCase):
    def test_geometry_can_pass_while_shared_frequency_fails(self):
        # At both ends these integer-frequency waves have the same coordinates.
        common=dict(k=1,phase_degrees=90,amplitude=1,clock_radians=0,count=2,stage=dict(x=0,y=0,width=100,height=100),points=[dict(index=0,x=6,y=6),dict(index=1,x=94,y=6)])
        one=dict(common,model='wave');two=dict(common,model='standing-wave')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'a.json').write_text(json.dumps(one));(root/'b.json').write_text(json.dumps(two));m=root/'index.json';m.write_text(json.dumps({'snapshots':['a.json','b.json']}))
            self.assertTrue(inspect_shared_batch(m)['ok'])
            two['k']=2
            self.assertTrue(inspect_snapshot(two,require_all=True)['ok'])
            (root/'b.json').write_text(json.dumps(two));self.assertFalse(inspect_shared_batch(m)['ok'])
            with contextlib.redirect_stdout(io.StringIO()):self.assertEqual(main([str(m)]),1)
            two=dict(one);(root/'b.json').write_text(json.dumps(two));self.assertFalse(inspect_shared_batch(m)['ok'])
            m.write_text(json.dumps({'snapshots':['a.json']}));self.assertFalse(inspect_shared_batch(m)['ok'])
            m.write_text(json.dumps({'snapshots':['../a.json','b.json']}));self.assertFalse(inspect_shared_batch(m)['ok'])
