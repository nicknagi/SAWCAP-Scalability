# The entrypoint for the sawcap project - this should be run on the runner i.e the node that monitors the cluster
# get_stacks.sh will be run on each of the workers
from entities.database import Database
from data_collector.collector import DataCollector
from time import sleep

class Sawcap:
    def __init__(self):
        self.database = Database()
        self.data_collector = DataCollector(["localhost"])

    def run(self):
        while True:
            # The logic for running everything
            x = self.data_collector.get_new_data(10)
            print(x)
            sleep(11)

if __name__ == "__main__":
    sawcap = Sawcap()
    sawcap.run()
