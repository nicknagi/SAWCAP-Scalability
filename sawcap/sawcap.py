# The entrypoint for the sawcap project - this should be run on the runner i.e the node that monitors the cluster
# get_stacks.sh will be run on each of the workers
from entities.database import Database
from data_collector.collector import DataCollector
from entities.snapshot_collection import SnapshotCollection
from time import sleep
from entities.workload import Workload

import warnings
warnings.filterwarnings('ignore')

WINDOW_SIZE = 10

class Sawcap:
    def __init__(self):
        self.database = Database()
        self.data_collector = DataCollector(["172.31.15.58"])
        self._current_workload_pid = "-1"
        self._current_workload = None

    def run(self):
        while True:
            # The logic for running everything
            data_from_workers = self.data_collector.get_new_data(WINDOW_SIZE)

            first_worker_data = data_from_workers[0]["data"]
            for window in first_worker_data:
                snapshot_collection = SnapshotCollection(WINDOW_SIZE, window["raw_resource_data"], window["stacktrace_data"])
                if window["pid"] != self._current_workload_pid:
                    self._current_workload_pid = window["pid"]
                    print(f"New Workload Detected PID: {self._current_workload_pid}")
                    self._current_workload = Workload(snapshot_collection, window["pid"])
                    self.database.add_new_workload(self._current_workload)
                else:
                    self._current_workload.add_new_snapshot_collection(snapshot_collection)

            print(self.database._database)
            print(self.database.get_uncharacterized_workloads()[0]._snapshot_collections)
            sleep(WINDOW_SIZE+1)

if __name__ == "__main__":
    sawcap = Sawcap()
    sawcap.run()
