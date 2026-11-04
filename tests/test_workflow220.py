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

    def test_batch_boolean(self):
        from tools.coordinate_batch import inspect_batch
        result=inspect_batch('/missing.json',require_all=1)
        self.assertFalse(result['ok'])
        self.assertEqual(result['checked_files'],0)
        self.assertIn('require_all',result['errors'][0])

    def test_scene_check(self):
        from tools.scene import main
        from tools.build import ROOT
        from contextlib import redirect_stdout
        from io import StringIO
        with redirect_stdout(StringIO()): self.assertEqual(main([str(ROOT/'qa/scene-example.json'),'--check']),0)

    def test_scene_canonical(self):
        from tools.scene import main
        from tools.build import ROOT
        from contextlib import redirect_stdout
        from io import StringIO
        import json
        out=StringIO()
        with redirect_stdout(out): self.assertEqual(main([str(ROOT/'qa/scene-example.json'),'--canonical']),0)
        self.assertEqual(json.loads(out.getvalue())['version'],1)

    def test_view_schema(self):
        from tools.scene import view_schema,validate_view
        schema=view_schema()
        for key, field in schema.items():
            values=field.get('choices',[True,False])
            for value in values:self.assertEqual(validate_view({key:value}),{key:value})
        self.assertTrue(schema['point-shape']['default'])

    def test_model_list(self):
        from tools.scene import main
        from contextlib import redirect_stdout
        from io import StringIO
        import json
        out=StringIO()
        with redirect_stdout(out):self.assertEqual(main(['--list-models']),0)
        self.assertIn('rose',json.loads(out.getvalue()))

    def test_scene_json_error(self):
        from tools.scene import main
        from contextlib import redirect_stdout
        from io import StringIO
        import json
        out=StringIO()
        with redirect_stdout(out): self.assertEqual(main(['/missing.json','--check','--json']),1)
        self.assertFalse(json.loads(out.getvalue())['ok'])

    def test_collection_schema(self):
        from tools.scene_collection import validate_collection
        scene=dict(version=1,model='rose')
        data=dict(version=1,title='作品集',scenes=[dict(id='rose',scene=scene)])
        self.assertEqual(validate_collection(data)['scenes'][0]['scene']['count'],192)
        for identifier in ('../escape','a/b','A','x'*49):
            with self.assertRaises(ValueError):validate_collection(dict(data,scenes=[dict(id=identifier,scene=scene)]))
        with self.assertRaises(ValueError):validate_collection(dict(data,scenes=data['scenes']*2))

    def test_collection_export(self):
        from tools.scene_collection import export_collection
        from pathlib import Path
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as folder:
            out=Path(folder)/'out'
            data=dict(version=1,title='作品',scenes=[dict(id='rose',scene=dict(version=1,model='rose',count=96))])
            export_collection(data,out)
            self.assertTrue((out/'rose/index.html').is_file())
            before=(out/'rose/index.html').read_bytes()
            with self.assertRaises(ValueError):export_collection(data,out)
            self.assertEqual(before,(out/'rose/index.html').read_bytes())

    def test_collection_index_escape(self):
        from tools.scene_collection import collection_index
        html=collection_index(dict(title='<作品>',scenes=[dict(id='one',scene=dict(title='<試験>',model='rose',count=96))]))
        self.assertIn('&lt;作品&gt;',html)
        self.assertIn('&lt;試験&gt;',html)
        self.assertIn('href="one/index.html"',html)
        self.assertNotIn('<script',html)

    def test_collection_hashes(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from tools.scene_collection import write_checksums
        import json,hashlib
        with TemporaryDirectory() as folder:
            p=Path(folder); (p/'index.html').write_text('abc')
            write_checksums(p)
            entry=json.loads((p/'checksums.json').read_text())['files'][0]
            self.assertEqual(entry['sha256'],hashlib.sha256(b'abc').hexdigest())
            self.assertEqual(entry['bytes'],3)

    def test_collection_verify(self):
        from tools.scene_collection import export_collection,verify_collection
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as folder:
            out=Path(folder)/'out'
            export_collection(dict(version=1,title='作品',scenes=[dict(id='rose',scene=dict(version=1,model='rose',count=96))]),out)
            self.assertTrue(verify_collection(out)['ok'])
            (out/'rose/index.html').write_text('changed')
            self.assertFalse(verify_collection(out)['ok'])

    def test_collection_cli_error(self):
        from tools.scene_collection import main
        from contextlib import redirect_stdout
        from io import StringIO
        import json
        out=StringIO()
        with redirect_stdout(out):self.assertEqual(main(['/missing','--verify']),1)
        self.assertFalse(json.loads(out.getvalue())['ok'])
