import unittest
from entities.snapshot_collection import SnapshotCollection
import numpy as np

class TestSnapshotCollection(unittest.TestCase):

    # Will replace this function with DataCollector class methods later
    def _create_snapshot_collection_helper(self, filename):
        with open("data_aggregator/tests/sample_data/"+filename, "r") as f:
            # Return a snapshot_collection with snapshot_collection size 1
            return SnapshotCollection(1, [[1,1]], [f.read()])

    def test_snapshot_collection_init(self):
        resource_data = [[1,2], [3,4], [1,2], [3,4]]
        expected_resource_data = [np.array([1,3,1,3]), np.array([2,4,2,4])]
        window_size = 4
        stacktrace_data = ["Hello", "world", "Hello", "world"]
        new_snapshot_collection = SnapshotCollection(window_size, resource_data, stacktrace_data)

        self.assertEqual(window_size, new_snapshot_collection.window_size)
        for p, q in zip(expected_resource_data, new_snapshot_collection.resource_data):
            np.testing.assert_almost_equal(p, q)
        self.assertEqual(stacktrace_data, new_snapshot_collection.stacktrace_data)
    
    def test_snapshot_collection_stacktrace_similarity_against_itself_is_same(self):
        snapshot_collection_1 = self._create_snapshot_collection_helper("threaddump_aggregate_simple")
        self.assertTrue(snapshot_collection_1.stacktrace_similarity(snapshot_collection_1) == 1)

    
    def test_snapshot_collection_stacktrace_similarity_(self):
        snapshot_collection_1 = self._create_snapshot_collection_helper("threaddump_aggregate_simple")
        self.assertTrue(snapshot_collection_1.stacktrace_similarity(snapshot_collection_1) == 1)