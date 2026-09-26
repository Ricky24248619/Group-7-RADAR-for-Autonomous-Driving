import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analyse_offroad_ground import GROUPS,LOOKUP,predicted_groups

class GroundTests(unittest.TestCase):
    def test_semantic_partition_does_not_turn_water_roots_or_unknown_into_floor(self):
        self.assertEqual(sum(map(len,GROUPS.values())),len(LOOKUP))
        self.assertEqual(len(LOOKUP),64)
        for label in ('water','tree_root','curb','undefined','high_grass'):
            self.assertNotEqual(LOOKUP[label],'ground_surface')

    def test_prediction_vegetation_and_other_remain_unresolved(self):
        r=predicted_groups(np.array([1,2,3,4,5,6,7,8]))
        self.assertEqual(r,dict(other=1,obstacle_category=21,ground_category=7,vegetation=7))
        self.assertEqual(sum(r.values()),36)

if __name__=='__main__':unittest.main()
