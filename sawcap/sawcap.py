# The entrypoint for the sawcap project - this should be run on the runner i.e the node that monitors the cluster
# monitor.sh will be run on each of the workers
from entities.database import Database
from data_collector.collector import DataCollector
from predictor.predictor import Predictor
from utils import SMAPE
from entities.snapshot import Snapshot
from time import sleep
from characterizer.characterizer import Characterizer
from config import INTERVAL, WORKERS, LOG_LEVEL, ENABLE_STATS
import logging

import numpy as np
import sys

logging.basicConfig(format='sawcap.py: %(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S', level=LOG_LEVEL)

# Data structure to hold data for calculating statistics
stats = {
    "actual_data": [],
    "predicted_data": []
}

class Sawcap:
    def __init__(self):
        self.database = Database()
        self.data_collector = DataCollector(WORKERS)
        self.characterizer = Characterizer(self.database)
        self.predictor = Predictor(self.database, "lasso")
        self.curr_phase = ""

    def run(self):
        while True:
            self._get_new_snapshot() # prev1 (prev 2 is last prev1)
            sleep(INTERVAL)
            self._get_new_snapshot() # curr

            # Check which phase we are in currently
            self.curr_phase = self.characterizer.get_current_phase()

            # Based on the current phase make a prediction
            predicted, phase_exists = self.predictor.get_prediction(self.curr_phase)
            
            # Log data for error calculation and print predictions
            if ENABLE_STATS:
                stats["predicted_data"].append(predicted[0])
                stats["actual_data"].append(self.database.get_triplets()[-1].resource_data)
                calculate_errors()

            logging.info("Actual: " + str(["{:.2f}".format(a) for a in self.database.get_curr_resource().resource_data]) + " Predicted:" + str(["{:.2f}".format(a) for a in predicted[0]]))
            anomaly_detected = self.predictor.detect_anomaly(predicted, self.database.get_curr_resource().resource_data, self.curr_phase, phase_exists)
            if anomaly_detected == True:
                handler()
            # Add profile to phase database
            self.characterizer.update_phase_database(self.curr_phase)

            # Update ML model for current phase, if possible
            self.predictor.update_ml_model(self.curr_phase)

    def _get_new_snapshot(self):
        stacktrace_functions, resource_data = self.data_collector.get_data_from_workers()
        snapshot = Snapshot(resource_data, stacktrace_functions)
        logging.debug("Added new snapshot to database")
        self.database.add_new_snapshot(snapshot)

    # Exit after catching a Keyboard Interrupt
def handler(signal_received = None, frame = None):
    calculate_errors()
    sys.exit(2)

def calculate_errors():
    print("\n### Error Rates ###")

    actual_resources = stats["actual_data"]
    predicted_resources = stats["predicted_data"]

    # CPU resource usage accuracy
    actual_resources_cpu = [resource[0] for resource in actual_resources]
    predicted_resources_cpu = [resource[0] for resource in predicted_resources]
    e_cpu = SMAPE(actual_resources_cpu, predicted_resources_cpu)
    logging.debug('Error CPU: %.3f %%' % (e_cpu))

    # Memory usage accuracy
    actual_resources_mem = [resource[1] for resource in actual_resources]
    predicted_resources_mem = [resource[1] for resource in predicted_resources]
    e_mem = SMAPE(actual_resources_mem, predicted_resources_mem)
    logging.debug('Error MEM: %.3f %%' % (e_mem))

if __name__ == "__main__":
    # for graceful exit
    from signal import signal, SIGINT
    signal(SIGINT, handler)

    sawcap = Sawcap()
    sawcap.run()
