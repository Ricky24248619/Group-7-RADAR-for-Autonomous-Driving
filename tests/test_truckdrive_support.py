import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from truckdrive_paired_support import annotation_pose_interpolator, calibration_transform, frame_index, valid_box
from compare_long_range_profiles import profile, timing_sensitivity


class TruckDriveSupportTests(unittest.TestCase):
    def test_timing_comparison_uses_same_annotations(self):
        row=dict(annotation_token='1',instance_token='a',scene='s',range_m=160,margin_m=0,
                 category='Vehicle-Passenger',lidar_points=0,radar_points=1)
        result=timing_sensitivity([row,dict(row,annotation_token='2')],[dict(row,lidar_points=3)])
        self.assertTrue(all(r['observations']==1 for r in result))
        with self.assertRaises(ValueError):timing_sensitivity([row],[dict(row,range_m=170)])
        with self.assertRaises(ValueError):timing_sensitivity([row],[dict(row,annotation_token='3')])

    def test_pose_interpolation_and_no_extrapolation(self):
        try:
            import scipy
        except ImportError:
            self.skipTest('Raw-data runtime provides SciPy')
        with tempfile.TemporaryDirectory() as d:
            annotations={}
            for i in range(2):
                pose=np.eye(4);pose[0,3]=i*10
                path=Path(d)/f'{i}.json';path.write_text(json.dumps([dict(velodyne2global=pose.tolist())]))
                annotations[i]=(i*1_000_000_000,path)
            interpolate=annotation_pose_interpolator(annotations)
            self.assertAlmostEqual(interpolate(500_000_000)[0,3],5)
            for t in [-1,1_000_000_001]:
                with self.assertRaises(ValueError):interpolate(t)

    def test_sentinel_and_invalid_boxes_excluded(self):
        box=dict(x=160,y=2,z=0,l=4,w=2,h=1.5,yaw=0)
        self.assertTrue(valid_box(box))
        for key,value in [('x',-1000),('h',-1),('yaw',float('nan'))]:
            self.assertFalse(valid_box(dict(box,**{key:value})))
        self.assertFalse(valid_box({}))

    def test_sync_matching_keeps_timestamp_and_rejects_ambiguity(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'0063_3172004958.json').write_text('[]')
            self.assertEqual(frame_index(root)[63][0],3172004958)
            (root/'0063_3172005000.json').write_text('[]')
            with self.assertRaises(ValueError):frame_index(root)

    def test_calibration_child_to_parent_and_inverse(self):
        try:
            import scipy
        except ImportError:
            self.skipTest('Raw-data runtime provides SciPy')
        records={'edge':dict(header=dict(frame_id='velodyne'),child_frame_id='radar',
            transform=dict(translation=dict(x=2,y=3,z=4),rotation=dict(x=0,y=0,z=0,w=1)))}
        forward=calibration_transform(records,'radar')
        np.testing.assert_allclose(forward[:3,3],[2,3,4])
        np.testing.assert_allclose(calibration_transform(records,'velodyne','radar')@forward,np.eye(4))
        with self.assertRaises(ValueError):calibration_transform(records,'absent')

    def test_profile_keeps_zeros_and_weights_each_track_equally(self):
        rows=[dict(instance_token=track,scene='s',range_m=160,lidar_points=l,radar_points=r)
              for track,l,r in [('a',0,0),('a',0,0),('a',6,1),('b',10,5)]]
        summary=profile(rows)
        self.assertEqual(summary['lidar_points_p50'],3)
        self.assertEqual(summary['radar_ge_5_percent'],25)
        self.assertAlmostEqual(summary['lidar_equal_track_percent'],100*2/3)
        self.assertEqual(summary['neither'],2)


if __name__=='__main__':unittest.main()
