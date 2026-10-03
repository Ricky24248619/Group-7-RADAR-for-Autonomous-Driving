"""Known geometry, footprint boundaries and missing evidence must stay distinct."""
from pathlib import Path
import sys
import unittest
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analyse_p5_navigation import surface_planes, footprint_counts, map_counts


class GeometryTests(unittest.TestCase):
    def test_tilted_plane_is_flat_and_rotation_invariant_rms(self):
        xy=np.array([[x,y] for x in (.05,.25,.45) for y in (.05,.25,.45)])
        xyz=np.column_stack([xy,xy[:,0]*.5+xy[:,1]*.3])
        result=surface_planes(xyz,np.ones(len(xyz),bool),.5)
        self.assertEqual(result['eligible_cells'],1)
        self.assertEqual(result['rms_le_002'],1)
        xyz[:,2]+=np.array([-.1,.1,0,.1,-.1,0,0,0,.1])
        self.assertEqual(surface_planes(xyz,np.ones(len(xyz),bool),.5)['rms_gt_005'],1)

    def test_sparse_line_and_empty_references_stay_unresolved(self):
        xyz=np.array([[.05+i*.05,.1,0] for i in range(6)])
        self.assertEqual(surface_planes(xyz,np.ones(6,bool),.5)['line_like_cells'],1)
        self.assertEqual(surface_planes(xyz[:4],np.ones(4,bool),.5)['sparse_cells'],1)
        self.assertEqual(surface_planes(xyz,np.zeros(6,bool),.5)['candidate_cells'],0)
        with self.assertRaises(ValueError):surface_planes(xyz,np.ones(6,bool),0)

    def test_footprints_keep_hazard_and_unknown_losses_separate(self):
        candidate=np.ones((5,5),bool)
        hazard=np.zeros((5,5),bool);hazard[2,2]=True
        result=footprint_counts(candidate,hazard,1)
        self.assertEqual(result['candidate_centres'],24)
        self.assertEqual(result['retained_footprints'],0)
        self.assertEqual(result['lost_to_hazard'],8)
        self.assertEqual(result['lost_to_missing_or_uncertain_support'],16)
        tiny=footprint_counts(candidate,hazard,0)
        self.assertEqual(tiny['retained_footprints'],24)
        self.assertEqual(tiny['lost_to_hazard'],0)

    def test_fully_observed_interior_and_negative_cells(self):
        result=footprint_counts(np.ones((5,5),bool),np.zeros((5,5),bool),1)
        self.assertEqual(result['retained_footprints'],9)
        points=np.array([[-.1,-.1,0],[.1,.1,0],[.1,.1,1]])
        rows=map_counts(points,np.array([1,1,3]),.5,radius=1)
        self.assertEqual(rows[0]['candidate_centres'],1)
        self.assertEqual(rows[0]['observed_roi_cells'],2)
        self.assertEqual(rows[0]['retained_footprints'],1)
        self.assertEqual(rows[1]['retained_footprints'],0)


if __name__=='__main__':unittest.main()
