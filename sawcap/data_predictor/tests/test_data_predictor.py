import unittest
from data_predictor.prediction_helper import DataPredictor
import numpy as np

class TestDataPredictor(unittest.TestCase):

    def _test_clustering(self, filename):
        test_data = np.random.rand(10,2)
        input_vector =  np.random.rand(1,2)

        pred = DataPredictor()
        pred.updateFeatureVectors(test_data)
        
        result = pred.recognizeWorkloads(input_vector)
        self.assertTrue(result)

   