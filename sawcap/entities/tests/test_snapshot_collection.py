import unittest
from entities.snapshot_collection import SnapshotCollection

class TestSnapshotCollection(unittest.TestCase):

    # Will replace this function with DataCollector class methods later
    def _create_snapshot_collection_helper(self, filename):
        with open("data_aggregator/tests/sample_data/"+filename, "r") as f:
            # Return a snapshot_collection with snapshot_collection size 1
            return SnapshotCollection(1, [[1, 1]], [f.read()])

    def test_snapshot_collection_init(self):
        resource_data = [[1,2], [3,4]]
        window_size = 10
        stacktrace_data = ["Hello", "world"]
        new_snapshot_collection = SnapshotCollection(window_size, resource_data, stacktrace_data)

        self.assertEqual(window_size, new_snapshot_collection.window_size)
        self.assertEqual(resource_data, new_snapshot_collection.resource_data)
        self.assertEqual(stacktrace_data, new_snapshot_collection.stacktrace_data)
    
    def test_snapshot_collection_stacktrace_similarity_against_itself_is_same(self):
        snapshot_collection_1 = self._create_snapshot_collection_helper("threaddump_aggregate_simple")
        self.assertTrue(snapshot_collection_1.stacktrace_similarity(snapshot_collection_1) == 1)

    
    def test_snapshot_collection_stacktrace_similarity_(self):
        snapshot_collection_1 = self._create_snapshot_collection_helper("threaddump_aggregate_simple")
        self.assertTrue(snapshot_collection_1.stacktrace_similarity(snapshot_collection_1) == 1)