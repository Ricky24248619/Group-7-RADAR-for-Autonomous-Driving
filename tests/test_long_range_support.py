import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_long_range_support import describe,one_per_instance
from audit_truckscenes_preprocessing import sector_mean_times
import numpy as np


class LongRangeTests(unittest.TestCase):
    def test_track_selection_is_time_based_not_support_based(self):
        rows=[dict(instance_token='a',timestamp=3,annotation_token='z',lidar_points=9),
              dict(instance_token='a',timestamp=1,annotation_token='b',lidar_points=0),
              dict(instance_token='a',timestamp=1,annotation_token='a',lidar_points=1),
              dict(instance_token='b',timestamp=2,annotation_token='c',lidar_points=0)]
        self.assertEqual([r['annotation_token'] for r in one_per_instance(rows)],['a','c'])

    def test_paired_difference_and_partition(self):
        rows=[dict(instance_token=str(i),scene='s',range_m=160+i,lidar_points=l,radar_points=r)
              for i,(l,r) in enumerate([(1,0),(0,1),(2,2),(0,0),(1,0)])]
        r=describe(rows)
        self.assertAlmostEqual(r['difference_pp'],20)
        self.assertEqual(sum(r[k] for k in ['both','neither','lidar_only','radar_only']),5)
        self.assertEqual(describe(rows,2)['both'],1)
        with self.assertRaises(ValueError):describe([])

    def test_sector_times_group_angles_without_changing_point_order(self):
        angles=np.deg2rad([45.2,46.1,45.8])
        points=np.array([np.cos(angles),np.sin(angles),np.zeros(3)])
        np.testing.assert_array_equal(sector_mean_times(points,[1000,3000,2000]),[1500,3000,1500])

    def test_sector_empty_and_bad_timestamp_input(self):
        self.assertEqual(len(sector_mean_times(np.empty((3,0)),[])),0)
        for times in [[],[float('nan')]]:
            with self.assertRaises(ValueError):sector_mean_times(np.zeros((3,1)),times)


if __name__=='__main__':unittest.main()
