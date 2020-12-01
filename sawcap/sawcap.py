# The entrypoint for the sawcap project - this should be run on the runner i.e the node that monitors the cluster
# get_stacks.sh will be run on each of the workers

from data_aggregator.data_aggregator import DataCollector
from entities.database import Database

class Sawcap:
    
    def __init__(self):
        self.database = Database()
    
    def run():
        while True:
            # The logic for running everything
            pass


if __name__ == "__main__":
    sawcap = Sawcap()
    sawcap.run()