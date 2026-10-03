import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from inspect_goose_error_cases import instance_counts


class InstanceTests(unittest.TestCase):
    def test_unassigned_ids_are_not_objects_and_partial_errors_keep_denominator(self):
        rows=instance_counts(np.array([0,0,7,7,8]),np.array([True,True,True,False,False]))
        self.assertEqual(rows,[dict(instance_id=7,points=2,ground_category_points=1),
                               dict(instance_id=8,points=1,ground_category_points=0)])


if __name__=='__main__':unittest.main()
