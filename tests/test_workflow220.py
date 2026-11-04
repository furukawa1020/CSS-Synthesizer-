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
