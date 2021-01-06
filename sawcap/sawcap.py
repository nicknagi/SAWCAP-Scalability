# The entrypoint for the sawcap project - this should be run on the runner i.e the node that monitors the cluster
# monitor.sh will be run on each of the workers
from entities.database import Database
from data_collector.collector import DataCollector
from predictor.predictor import Predictor
from entities.snapshot import Snapshot
from time import sleep
from characterizer.characterizer import Characterizer
from config import INTERVAL, WORKERS, LOG_LEVEL
import logging
import sys
from signal import signal, SIGINT
from sys import exit

logging.basicConfig(format='sawcap.py: %(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S', level=LOG_LEVEL)

class Sawcap:
    def __init__(self):
        self.database = Database()
        self.data_collector = DataCollector(WORKERS)
        self.characterizer = Characterizer(self.database)
        self.predictor = Predictor()
        self.get_accuracy = False

        # for graceful exit
        signal(SIGINT, handler)

        # prediction algorithm to use
        self.predictor.set_algo(sys.argv[1])

        # determine whether we need to calculate accuracy or not
        if len(sys.argv) == 3:
            self.get_accuracy = bool(int(sys.argv[2]))    # takes a 0 or 1 from cmd line


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

    # Exit after catching a Keyboard Interrupt
    def handler(self, signal_received, frame):
        actual_resources = self.predictor.get_actual_resources()
        predicted_resources = self.predictor.get_predicted_resources()
        
        if (self.get_accuracy and actual_resources and predicted_resources):
            print("\n### Error Rates ###")

            # CPU resource usage accuracy
            actual_resources_cpu = [resource[0] for resource in actual_resources]
            predicted_resources_cpu = [resource[0] for resource in predicted_resources]
            e_cpu = self.predictor.SMAPE(actual_resources_cpu, predicted_resources_cpu)
            print('Error CPU: %.3f %%' % (e_cpu))

            # Memory usage accuracy
            actual_resources_mem = [resource[1] for resource in actual_resources]
            predicted_resources_mem = [resource[1] for resource in predicted_resources]
            e_mem = self.predictor.SMAPE(actual_resources_mem, predicted_resources_mem)
            print('Error MEM: %.3f %%' % (e_mem))

        sys.exit(2)

    # Exit gracefully after detecting an anomaly
    def print_and_exit(self, code):
        actual_resources = self.predictor.get_actual_resources()
        predicted_resources = self.predictor.get_predicted_resources()

        if (self.get_accuracy and actual_resources and predicted_resources):
            print("\n### Error Rates ###")

            # CPU resource usage accuracy
            actual_resources_cpu = [resource[0] for resource in actual_resources]
            predicted_resources_cpu = [resource[0] for resource in predicted_resources]
            e_cpu = self.predictor.SMAPE(actual_resources_cpu, predicted_resources_cpu)
            print('Error CPU: %.3f %%' % (e_cpu))

            # Memory usage accuracy
            actual_resources_mem = [resource[1] for resource in actual_resources]
            predicted_resources_mem = [resource[1] for resource in predicted_resources]
            e_mem = self.predictor.SMAPE(actual_resources_mem, predicted_resources_mem)
            print('Error MEM: %.3f %%' % (e_mem))

        sys.exit(code)


if __name__ == "__main__":
    sawcap = Sawcap()
    sawcap.run()


