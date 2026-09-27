from pathlib import Path
import sys
import tempfile
import csv
import json
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analyse_radiate_fog import inside,rotate_control,radar_contrast,timestamps,lidar_pixels,RES


class RadiateTests(unittest.TestCase):
    def test_evidence_has_paired_denominators_and_expansion_cannot_lose_points(self):
        root=Path(__file__).resolve().parents[1]/'docs/evidence/radiate-fog'
        manifest=json.loads((root/'manifest.json').read_text())
        with (root/'frames.csv').open(newline='') as file:frames=list(csv.DictReader(file))
        self.assertEqual(len(frames),manifest['frames'])
        self.assertEqual(len(frames)+len(manifest['excluded']),manifest['available_radar_frames'])
        self.assertTrue(all(abs(float(r['delta_ms']))<=50 for r in frames))
        with (root/'observations.csv').open(newline='') as file:rows=list(csv.DictReader(file))
        lookup={(r['frame'],r['track'],r['margin_m']):r for r in rows}
        self.assertEqual(len(lookup),len(rows))
        for r in rows:
            self.assertIn(r['frame'],{f['frame'] for f in frames})
            self.assertLessEqual(int(r['lidar_above_ground_returns']),int(r['lidar_all_returns']))
            self.assertLessEqual(int(r['radar_contrast_gap20']),int(r['radar_contrast_gap10']))
            if r['margin_m']=='0':
                expanded=lookup[r['frame'],r['track'],'1']
                self.assertLessEqual(int(r['lidar_above_ground_returns']),int(expanded['lidar_above_ground_returns']))
                self.assertLessEqual(int(r['lidar_above_ground_returns']),int(r['adjacent_scan_max_returns']))

    def test_rotated_box_uses_sdk_clockwise_image_convention(self):
        box=dict(position=[570,570,12,4],rotation=90)
        np.testing.assert_array_equal(inside(np.array([[576,577],[581,572],[576,565]]),box),[True,False,False])

    def test_control_preserves_range_and_dimensions(self):
        box=dict(position=[600,200,10,20],rotation=30)
        control=rotate_control(box,90)
        a=np.array(box['position'][:2])+np.array(box['position'][2:])/2-576
        b=np.array(control['position'][:2])+np.array(control['position'][2:])/2-576
        self.assertAlmostEqual(np.linalg.norm(a),np.linalg.norm(b))
        self.assertEqual(control['rotation'],-60)
        self.assertEqual(control['position'][2:],box['position'][2:])

    def test_flat_image_has_no_contrast_but_bright_target_does(self):
        image=np.full((1152,1152),20,dtype=np.uint8)
        box=dict(position=[570,570,12,12],rotation=0)
        self.assertEqual(radar_contrast(image,box,[box])['radar_contrast_pass'],0)
        image[570:583,570:583]=100
        self.assertEqual(radar_contrast(image,box,[box])['radar_contrast_gap20'],1)
        self.assertIsNone(radar_contrast(image,box,[box],exclude_target_overlap=True))

    def test_timestamp_precision_and_published_translation(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'times.txt';path.write_text('Frame: 000001 Time: 1574859771.744660272\n')
            self.assertEqual(timestamps(path),[(1,1574859771744660272)])
        np.testing.assert_allclose(lidar_pixels(np.zeros((1,5)))[0],[576+.6003/RES,576+.120102/RES])


if __name__=='__main__':unittest.main()
