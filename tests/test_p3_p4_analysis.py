"""Regression checks for temporal and terrain information that summaries can lose."""
import sys
from pathlib import Path
import unittest
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analyse_p3_p4_road import episodes, support_counts, temporal
from analyse_p3_p4_terrain import cell_counts, policy_groups


class TemporalTests(unittest.TestCase):
    def test_missing_sample_failure_and_long_time_gap(self):
        rows = [dict(position=i,time_s=t,yes=yes) for i,t,yes in
                [(0,0,True),(1,1,True),(3,3,True),(4,4,False),(5,5,True),(6,8,True),(7,9,True)]]
        self.assertEqual([len(r) for r in episodes(rows,lambda r:r['yes'],1)],[2,1,1,2])

    def test_forward_boundary_scene_identity_and_confirmation(self):
        rows = [dict(scene=scene,instance_token='same',category='Vehicle-Car',position=i,time_s=i,
                     margin_m='0',azimuth_deg=angle,range_m=300-10*i,lidar_points='3',radar_points='1')
                for scene,angle in [('a',15),('b',-15),('c',15.001)] for i in range(3)]
        tracks,runs,summary = temporal(rows,'test','aligned',0,3,15,dict(a=1,b=1,c=1))
        self.assertEqual(summary['tracks'],2)
        self.assertEqual(summary['lidar_persistent_tracks'],2)
        self.assertEqual(summary['radar_persistent_tracks'],0)
        self.assertEqual([r['confirmation_range_m'] for r in tracks if r['sensor']=='lidar'],[280,280])
        self.assertEqual([r['confirmation_delay_s'] for r in tracks if r['sensor']=='lidar'],[2,2])

    def test_presence_partitions_and_validation(self):
        rows = [dict(scene='a',instance_token=str(i),lidar_points=l,radar_points=r)
                for i,(l,r) in enumerate([(0,0),(1,0),(0,1),(1,1)])]
        self.assertEqual(support_counts(rows,1)['union'],3)
        rows[0]['radar_points']=-1
        with self.assertRaises(ValueError):support_counts(rows,1)


class TerrainTests(unittest.TestCase):
    def test_fine_policy_preserves_water_vegetation_and_ignored(self):
        policy = [dict(label_key=k,traversability_id=0) for k in range(64)]
        for k in (1,16,17,27,54,59):policy[k]['traversability_id']=3
        policy[31]['traversability_id']=1
        policy[51]['traversability_id']=2
        groups = policy_groups(policy)
        self.assertEqual(groups[[0,1,16,31,51,54]].tolist(),[0,3,5,1,2,4])
        with self.assertRaises(ValueError):policy_groups(policy[:-1])

    def test_majority_loses_correctly_labelled_hazard_and_negative_cells(self):
        xyz = np.array([[-.2,-.2,0],[-.3,-.3,0],[-.4,-.4,.2],[.2,.2,0]])
        group = np.array([1,1,3,1]); pred = np.array([3,3,4,3])
        counts = cell_counts(xyz,group,pred,.5)
        self.assertEqual(counts['observed_cells'],2)
        self.assertEqual(counts['mixed_firm_rigid_cells'],1)
        self.assertEqual(counts['mixed_true_firm_majority_cells'],1)
        self.assertEqual(counts['mixed_predicted_ground_majority_cells'],1)

    def test_unobserved_cells_never_counted_and_ties_not_majority(self):
        counts = cell_counts(np.array([[0,0,0],[0,0,.2],[100,100,0]]),np.array([1,3,0]),np.array([3,4,0]),1)
        self.assertEqual(counts['observed_cells'],2)
        self.assertEqual(counts['mixed_true_firm_majority_cells'],0)
        self.assertEqual(counts['mixed_predicted_ground_majority_cells'],0)


if __name__=='__main__':unittest.main()
