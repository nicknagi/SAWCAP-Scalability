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

import numpy as np
import sys

logging.basicConfig(format='sawcap.py: %(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S', level=LOG_LEVEL)

#Stats
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
            self._get_new_snapshot()
            sleep(INTERVAL)
            self._get_new_snapshot()

            self.curr_phase = self.characterizer.get_current_phase()
            predicted = self.predictor.get_prediction(self.curr_phase)

            stats["predicted_data"].append(predicted[0])
            stats["actual_data"].append(self.database.get_triplets()[-1].resource_data)
            calculate_errors()
            logging.info("Actual: " + str(["{:.2f}".format(a) for a in self.database.get_triplets()[-1].resource_data]) + " Predicted:" + str(["{:.2f}".format(a) for a in predicted[0]]))
            
            self.characterizer.update_phase_database(self.curr_phase)
            self.predictor.update_ml_model(self.curr_phase)

    def _get_new_snapshot(self):
        stacktrace_functions, resource_data = self.data_collector.get_data_from_workers()
        snapshot = Snapshot(resource_data, stacktrace_functions)
        logging.debug("Added new snapshot to database")
        self.database.add_new_snapshot(snapshot)

    # Exit after catching a Keyboard Interrupt
def handler(signal_received, frame):
    calculate_errors()
    sys.exit(2)
    
def SMAPE(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred) # convert to numpy arrays
    return np.mean(np.abs(y_true - y_pred) / (np.abs(y_true) + np.abs(y_pred) + 1e-8)) * 100

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
