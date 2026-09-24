import pickle
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_detector_compatibility import checkpoint_configs, input_range, in_input_roi


class CompatibilityTests(unittest.TestCase):
    def test_config_is_parsed_without_executing_statements(self):
        self.assertEqual(input_range("raise RuntimeError('never execute')\npoint_cloud_range=[0,-40,-4,70,40,2]"),[0,-40,-4,70,40,2])
        with self.assertRaises(ValueError): input_range('point_cloud_range=unknown()')
        with self.assertRaises(ValueError): input_range('point_cloud_range=[0,0,0,0,1,1]')

    def test_checkpoint_config_extraction_without_unpickling(self):
        text='model = dict()\npoint_cloud_range=[0,-40,-4,70,40,2]'
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'model.pth'
            with zipfile.ZipFile(path,'w') as archive:
                archive.writestr('archive/data.pkl',pickle.dumps({'meta':{'config':text}}))
            self.assertEqual(checkpoint_configs(path),[text])

    def test_roi_is_rectangular_not_planar_radius(self):
        roi=[0,-40,-4,70,40,2]
        self.assertTrue(in_input_roi([69,39,100],roi))
        self.assertFalse(in_input_roi([69,39,100],roi,3))
        self.assertFalse(in_input_roi([70,0,0],roi))
        self.assertFalse(in_input_roi([-1,0,0],roi))
        self.assertFalse(in_input_roi([0,41,0],roi))


if __name__=='__main__': unittest.main()
