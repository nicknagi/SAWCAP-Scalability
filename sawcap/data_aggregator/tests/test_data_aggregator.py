import unittest
from data_aggregator.data_aggregator import DataAggregator
from entities.snapshot import Snapshot

class TestDataAggregator(unittest.TestCase):

    # Will replace this function with DataCollector class methods later
    def _create_snapshot_helper(self, filename):
        with open("data_aggregator/tests/sample_data/"+filename, "r") as f:
            # Return a snapshot with window size 1
            return Snapshot(1, [[1, 1]], [f.read()])

    def test_generate_histograms_and_unique_stacktraces_function_no_duplicates(self):
        snapshot = self._create_snapshot_helper("threaddump_aggregate_simple")
        data_aggregator = DataAggregator(snapshot)

        actual_data = data_aggregator.generate_histograms_and_unique_stacktraces()
        expected_data = ([" - org.apache.spark.executor.CoarseGrainedExecutorBackend.main(CoarseGrainedExecutorBackend.scala)"], [1])
        self.assertEqual(actual_data, expected_data)

    def test_generate_histograms_and_unique_stacktraces_function_duplicates(self):
        snapshot = self._create_snapshot_helper("threaddump_aggregate_duplicate")
        data_aggregator = DataAggregator(snapshot)

        actual_data = data_aggregator.generate_histograms_and_unique_stacktraces()
        expected_data = ([" - org.apache.spark.executor.CoarseGrainedExecutorBackend.main(CoarseGrainedExecutorBackend.scala)"], [3])
        self.assertEqual(actual_data, expected_data)
