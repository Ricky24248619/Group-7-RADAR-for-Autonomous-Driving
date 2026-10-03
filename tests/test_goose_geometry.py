import sys
from pathlib import Path
import unittest
import importlib.util
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from diagnose_goose_geometry import mixed_reference_voxels,local_orientation


class GeometryTests(unittest.TestCase):
    def test_voxel_collision_requires_same_xyz_cell(self):
        xyz=np.array([[0.,0.,0.],[.01,.01,.01],[.03,.01,.01],[-.01,0,0]])
        self.assertEqual(mixed_reference_voxels(xyz,np.array([True,False,False,False]),.025).tolist(),[True,True,False,False])

    @unittest.skipUnless(importlib.util.find_spec('scipy'),'Requires optional SciPy analysis dependency')
    def test_normals_distinguish_horizontal_vertical_and_sparse(self):
        a,b=np.meshgrid(np.linspace(-.1,.1,5),np.linspace(-.1,.1,5))
        flat=np.c_[a.ravel(),b.ravel(),np.zeros(a.size)]
        self.assertAlmostEqual(local_orientation(flat,np.zeros((1,3)))[0],1)
        wall=flat[:,[2,0,1]]
        self.assertAlmostEqual(local_orientation(wall,np.zeros((1,3)))[0],0)
        self.assertTrue(np.isnan(local_orientation(flat,np.array([[9.,9.,9.]]))[0]))


if __name__=='__main__':unittest.main()
