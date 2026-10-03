import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from compare_goose_context import canonical_config


class ContextTests(unittest.TestCase):
    def test_only_output_and_patch_differences_are_removed(self):
        a="save_path = 'a'\nseed = 1\nenc_patch_size=[64, 64]\ndec_patch_size=[64]"
        b=a.replace("'a'","'b'").replace('64','128')
        self.assertEqual(canonical_config(a),canonical_config(b))
        self.assertNotEqual(canonical_config(a),canonical_config(b.replace('seed = 1','seed = 2')))
        with self.assertRaises(ValueError):canonical_config('unrecognised configuration')


if __name__=='__main__':unittest.main()
