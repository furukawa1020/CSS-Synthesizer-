import unittest

class Workflow220Tests(unittest.TestCase):

    def test_deep_json(self):
        from tools.json_data import loads_json
        with self.assertRaisesRegex(ValueError, '深すぎ'):
            loads_json('['*2000+'0'+']'*2000)

    def test_bounded_json(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from tools.json_data import load_bounded_json
        with TemporaryDirectory() as folder:
            p=Path(folder)/'a.json'; p.write_text('{}')
            self.assertEqual(load_bounded_json(p,2),{})
            with self.assertRaises(ValueError): load_bounded_json(p,1)
            link=Path(folder)/'link.json'; link.symlink_to(p)
            with self.assertRaises(ValueError): load_bounded_json(link,100)

    def test_coordinate_cli_limit(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from contextlib import redirect_stdout
        from io import StringIO
        from tools.coordinates import main
        with TemporaryDirectory() as folder:
            p=Path(folder)/'a.json'; p.write_text(' '*(2*1024*1024+1))
            out=StringIO()
            with redirect_stdout(out): self.assertEqual(main([str(p)]),1)
            self.assertIn('サイズ上限',out.getvalue())

    def test_tangent_cli_limit(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from contextlib import redirect_stdout
        from io import StringIO
        from tools.tangents import main
        with TemporaryDirectory() as folder:
            p=Path(folder)/'a.json'; p.write_text(' '*(2*1024*1024+1))
            out=StringIO()
            with redirect_stdout(out): self.assertEqual(main([str(p)]),1)
            self.assertIn('サイズ上限',out.getvalue())

    def test_large_rotation(self):
        from tools.coordinates import inspect_snapshot
        import math
        rotation=1e308
        angle=math.radians(rotation%360)
        snapshot=dict(model='wave',k=1,phase_degrees=0,amplitude=1,clock_radians=0,count=2,stage=dict(x=0,y=0,width=100,height=100),rotation_degrees=rotation,points=[dict(index=0,x=50-44*math.cos(angle),y=50+44*math.sin(angle))])
        self.assertTrue(inspect_snapshot(snapshot)['ok'])
