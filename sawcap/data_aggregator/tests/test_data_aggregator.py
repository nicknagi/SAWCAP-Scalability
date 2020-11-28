import unittest
from data_aggregator.data_aggregator import DataAggregator
from entities.snapshot import Snapshot

class TestDataAggregator(unittest.TestCase):

    # Will replace this function with DataCollector class methods later
    def _create_snapshot_helper(self):
        with open("data_aggregator/tests/sample_data/threaddump_aggregate_0", "r") as f:
            return Snapshot(1, [[1,1]], [f.read()]) # Return a snapshot with window size 1

    def test_histograms_function(self):
        snapshot = self._create_snapshot_helper()
        data_aggregator = DataAggregator()

        data_aggregator.aggregate(snapshot)
        expected_data = [{" - org.apache.spark.executor.CoarseGrainedExecutorBackend.main(CoarseGrainedExecutorBackend.scala)": 1}]
        self.assertEqual(data_aggregator._histograms, expected_data)