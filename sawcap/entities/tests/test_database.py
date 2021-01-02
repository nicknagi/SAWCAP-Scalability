import unittest
from entities.database import Database
from entities.snapshot_collection import SnapshotCollection
from entities.workload import Workload

class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.database = Database()
        self.workload1 = self._create_workload_helper()
        self.workload2 = self._create_workload_helper()

    def _create_workload_helper(self):
        return Workload(SnapshotCollection(1, [[1,1]], ["hello world"]), "123asdad")

    def test_characterization_queue_works(self):
        self.database.add_new_uncharacterized_workload(self.workload1)
        self.assertIn(self.workload1, self.database.get_uncharacterized_workloads())
        self.assertNotIn(self.workload2, self.database.get_uncharacterized_workloads())

        self.database.add_new_uncharacterized_workload(self.workload2)
        self.assertIn(self.workload1, self.database.get_uncharacterized_workloads())
        self.assertIn(self.workload2, self.database.get_uncharacterized_workloads())
    
    def test_can_remove_workloads_from_characterization_queue(self):
        self.database.add_new_uncharacterized_workload(self.workload1)
        self.database.add_new_uncharacterized_workload(self.workload2)

        self.assertIn(self.workload1, self.database.get_uncharacterized_workloads())
        self.assertIn(self.workload2, self.database.get_uncharacterized_workloads())

        self.database.remove_workload_from_characterization_queue(self.workload1)
        self.assertIn(self.workload2, self.database.get_uncharacterized_workloads())
        self.assertNotIn(self.workload1, self.database.get_uncharacterized_workloads())
