# The entrypoint for the sawcap project - this should be run on the runner i.e the node that monitors the cluster
# get_stacks.sh will be run on each of the workers
from entities.database import Database
from data_collector.collector import DataCollector
from entities.snapshot_collection import SnapshotCollection
from time import sleep

class Sawcap:
    def __init__(self):
        self.database = Database()
        self.data_collector = DataCollector(["172.31.15.58"])

    def run(self):
        while True:
            # The logic for running everything
            from pprint import pprint
            x = self.data_collector.get_new_data(10)
            raw_resource_data = x[0][1]["raw_resource_data"]
            for resource_window in raw_resource_data:
                print(SnapshotCollection(10, resource_window, ["hello"]*10).resource_aggregation)
            sleep(11)

if __name__ == "__main__":
    sawcap = Sawcap()
    sawcap.run()
