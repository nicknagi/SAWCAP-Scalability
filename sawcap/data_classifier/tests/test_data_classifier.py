import unittest
from data_classifier.classification_helper import DataClassifier
import numpy as np

class TestDataClassifier(unittest.TestCase):

    def _test_clustering(self, filename):
        test_data = np.random.rand(10,2)
        input_vector =  np.random.rand(1,2)

        pred = DataClassifier()
        pred.updateFeatureVectors(test_data)
        
        result = pred.recognizeWorkloads(input_vector)
        self.assertTrue(result)

   