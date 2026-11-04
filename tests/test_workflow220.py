import unittest

class Workflow220Tests(unittest.TestCase):

    def test_deep_json(self):
        from tools.json_data import loads_json
        with self.assertRaisesRegex(ValueError, '深すぎ'):
            loads_json('['*2000+'0'+']'*2000)
