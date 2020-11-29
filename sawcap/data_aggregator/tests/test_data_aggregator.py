import unittest
from data_aggregator.data_aggregator import DataAggregator
from entities.window import Window

class TestDataAggregator(unittest.TestCase):

    # Will replace this function with DataCollector class methods later
    def _create_window_helper(self, filename):
        with open("data_aggregator/tests/sample_data/"+filename, "r") as f:
            # Return a window with window size 1
            return Window(1, [[1, 1]], [f.read()])

    def test_generate_histograms_and_unique_stacktraces_function_no_duplicates(self):
        window = self._create_window_helper("threaddump_aggregate_simple")
        data_aggregator = DataAggregator(window)

        actual_data = data_aggregator.generate_histograms_and_unique_stacktraces()
        expected_data = ([" - org.apache.spark.executor.CoarseGrainedExecutorBackend.main(CoarseGrainedExecutorBackend.scala)"], [1])
        self.assertEqual(actual_data, expected_data)

    def test_generate_histograms_and_unique_stacktraces_function_duplicates(self):
        window = self._create_window_helper("threaddump_aggregate_duplicate")
        data_aggregator = DataAggregator(window)

        actual_data = data_aggregator.generate_histograms_and_unique_stacktraces()
        expected_data = ([" - org.apache.spark.executor.CoarseGrainedExecutorBackend.main(CoarseGrainedExecutorBackend.scala)"], [3])
        self.assertEqual(actual_data, expected_data)
