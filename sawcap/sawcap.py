# The entrypoint for the sawcap project - this should be run on the runner i.e the node that monitors the cluster
# monitor.sh will be run on each of the workers
from entities.database import Database
from data_collector.collector import DataCollector
from predictor.predictor import Predictor
from entities.snapshot import Snapshot
from time import sleep
from characterizer.characterizer import Characterizer
from config import INTERVAL, WORKERS, LOG_LEVEL, ENABLE_STATS, DATA_DIR, STATS_FILE
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
            predicted = self.predictor.get_prediction(self.curr_phase)
            
            # Log data for error calculation and print predictions
            if ENABLE_STATS:
                stats["predicted_data"].append(predicted[0])
                stats["actual_data"].append(self.database.get_triplets()[-1].resource_data)
                calculate_errors()

            logging.info("Actual: " + str(["{:.2f}".format(a) for a in self.database.get_curr_resource().resource_data]) + " Predicted:" + str(["{:.2f}".format(a) for a in predicted[0]]))
            
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
def handler(signal_received, frame):
    export_stats()
    sys.exit(2)
    
def SMAPE(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred) # convert to numpy arrays
    return np.mean(np.abs(y_true - y_pred) / (np.abs(y_true) + np.abs(y_pred) + 1e-8)) * 100

def calculate_errors():
    logging.info("\n### Accuracy Rates ###")

    actual_resources = stats["actual_data"]
    predicted_resources = stats["predicted_data"]

    # CPU resource usage accuracy
    actual_resources_cpu = [resource[0] for resource in actual_resources]
    predicted_resources_cpu = [resource[0] for resource in predicted_resources]
    acc_cpu = 100 - SMAPE(actual_resources_cpu, predicted_resources_cpu)
    logging.info('CPU Prediction Accuracy: %.3f %%' % (acc_cpu))

    # Memory usage accuracy
    actual_resources_mem = [resource[1] for resource in actual_resources]
    predicted_resources_mem = [resource[1] for resource in predicted_resources]
    acc_mem = 100 - SMAPE(actual_resources_mem, predicted_resources_mem)
    logging.info('MEM Prediction Accuracy: %.3f %%' % (acc_mem))

    return acc_cpu, acc_mem

def export_stats():
    acc_cpu, acc_mem = calculate_errors()
    file_path = DATA_DIR + STATS_FILE

    f = open(file_path, "a")
    f.write("\n### Accuracy Rates ###\n")
    f.write(f'CPU Prediction Accuracy: {acc_cpu:.3f}\n')
    f.write(f'MEM Prediction Accuracy: {acc_mem:.3f}\n')
    f.close()

if __name__ == "__main__":
    # for graceful exit
    from signal import signal, SIGINT, SIGTERM
    signal(SIGINT, handler)
    signal(SIGTERM, handler)

    sawcap = Sawcap()
    sawcap.run()

