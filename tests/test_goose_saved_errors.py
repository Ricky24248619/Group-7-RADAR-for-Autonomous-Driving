import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analyse_goose_saved_errors import confusion, verify_selection
from prepare_goose_subset import interior_indices,neighbor_indices

class SavedErrorsTests(unittest.TestCase):
    def test_neighbor_subset_requires_unique_interior_center(self):
        scans=list(map(Path,['a.bin','b.bin','c.bin','d.bin']))
        self.assertEqual(neighbor_indices(scans,'b.bin'),[0,1,2])
        for center in ('a.bin','d.bin','missing.bin'):
            with self.assertRaises(ValueError):neighbor_indices(scans,center)
        with self.assertRaises(ValueError):neighbor_indices([Path('b.bin')]*3,'b.bin')
    def test_stratified_selection_is_spaced_and_unique(self):
        self.assertEqual(interior_indices(100,3),[25,50,75])
        self.assertEqual(interior_indices(3,3),[0,1,2])
        for length,count in ((2,3),(20,0)):
            with self.assertRaises(ValueError):interior_indices(length,count)

    def test_planned_subset_rejects_partial_extra_and_changed_inputs(self):
        import copy
        entry=dict(frame='a.bin',sha256=dict(scan='a',label='b',challenge_label='c'))
        selection=dict(inputs=[entry],frames=1,points=4)
        verify_selection(selection,[entry],4)
        changed=copy.deepcopy(entry);changed['sha256']['scan']='changed'
        for inputs,points in (([],0),([entry,entry],8),([changed],4),([entry],3)):
            with self.assertRaises(ValueError):verify_selection(selection,inputs,points)

    def test_confusion_rows_are_truth_columns_are_prediction(self):
        m=confusion(np.array([2,2,3]),np.array([2,3,2]))
        self.assertEqual(m[2,3],1)
        self.assertEqual(m[3,2],1)
        self.assertEqual(m.trace(),1)
        self.assertEqual(m.sum(),3)
    def test_invalid_or_misaligned_predictions_rejected(self):
        for pred in (np.array([8]),np.array([-1]),np.array([2,3]),np.array([2.0])):
            with self.assertRaises(ValueError):confusion(np.array([2]),pred)
        with self.assertRaises(ValueError):confusion(np.array([2.0]),np.array([2]))
        self.assertEqual(confusion(np.array([],dtype=int),np.array([],dtype=int)).sum(),0)

if __name__=='__main__':unittest.main()
