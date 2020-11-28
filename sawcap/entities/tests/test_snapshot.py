import unittest
from entities.snapshot import Snapshot

class TestSnapshot(unittest.TestCase):

    def test_snapshot_init(self):
        resource_data = [[1,2], [3,4]]
        window_size = 10
        stacktrace_data = ["Hello", "world"]
        new_snapshot = Snapshot(window_size, resource_data, stacktrace_data)

        self.assertEqual(window_size, new_snapshot.window_size)
        self.assertEqual(resource_data, new_snapshot.resource_data)
        self.assertEqual(stacktrace_data, new_snapshot.stacktrace_data)