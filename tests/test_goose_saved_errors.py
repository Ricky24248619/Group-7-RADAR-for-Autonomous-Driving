import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analyse_goose_saved_errors import confusion

class SavedErrorsTests(unittest.TestCase):
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
