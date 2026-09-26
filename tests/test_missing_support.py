import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analyse_missing_support import breakdown, paired_tracks

def row(track,distance,lidar,radar,category='car'):
    return dict(instance_token=track,scene='scene',range_m=distance,lidar_points=lidar,radar_points=radar,category=category)

class MissingSupportTests(unittest.TestCase):
    def test_zero_returns_stay_in_class_denominator(self):
        r=breakdown([row('a',20,3,0),row('b',20,0,1)])
        self.assertEqual(r['lidar_missing_percent'],50)
        self.assertEqual(r['radar_only'],1)
        self.assertEqual(r['lidar_points_p50'],1.5)

    def test_only_same_tracks_in_both_bands_and_boundary_is_half_open(self):
        rows=[row('a',10,1,1),row('a',50,1,0),row('b',10,1,1)]
        pairs=paired_tracks(rows,(0,50),(50,100))
        self.assertEqual(len(pairs),1)
        self.assertEqual(pairs[0]['radar_far_minus_near_pp'],-100)
        self.assertEqual(pairs[0]['lidar_far_minus_near_pp'],0)

    def test_class_changing_track_is_not_mixed(self):
        self.assertEqual(paired_tracks([row('a',10,1,1),row('a',70,1,1,'truck')],(0,50),(50,100)),[])

if __name__=='__main__':unittest.main()
