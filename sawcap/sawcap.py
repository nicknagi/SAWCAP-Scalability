# The entrypoint for the sawcap project - this should be run on the runner i.e the node that monitors the cluster
# monitor.sh will be run on each of the workers
from entities.database import Database
from data_collector.collector import DataCollector
from entities.snapshot import Snapshot
from time import sleep
from characterizer.characterizer import Characterizer
from config import INTERVAL, WORKERS, LOG_LEVEL
import logging

logging.basicConfig(format='sawcap.py: %(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S', level=LOG_LEVEL)

class Sawcap:
    def __init__(self):
        self.database = Database()
        self.data_collector = DataCollector(WORKERS)
        self.characterizer = Characterizer(self.database)

    def run(self):
        while True:
            self._get_new_snapshot()
            sleep(INTERVAL)
            self._get_new_snapshot()
            self.characterizer.run()

    def _get_new_snapshot(self):
        stacktrace_functions, resource_data = self.data_collector.get_data_from_workers()
        snapshot = Snapshot(resource_data, stacktrace_functions)
        logging.debug("Added new snapshot to database")
        self.database.add_new_snapshot(snapshot)

if __name__ == "__main__":
    sawcap = Sawcap()
    sawcap.run()
