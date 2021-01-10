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
from signal import signal, SIGINT

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
    def __init__(self, datadir, algo):
        self.datadir = datadir
        self.algo = algo
        self.database = Database()
        self.data_collector = DataCollector(WORKERS)
        self.characterizer = Characterizer(self.database)
        self.predictor = Predictor(self.database, self.algo)
        self.curr_phase = ""

        logging.info("\nReloading phase DB")
        self.database.load_database(self.datadir, self.algo)
        # for graceful exit
        signal(SIGINT, self.sawcap_exit)


    def run(self):
        while True:
            self._get_new_snapshot() # prev1 (prev 2 is last prev1)
            sleep(INTERVAL)
            self._get_new_snapshot() # curr

            triplets = self.database.get_triplets()
            if len(triplets[1].stacktrace_data)==0 and len(triplets[2].stacktrace_data)==0:
                logging.warning("There are no stacktraces in the workload, no predictions are made")
                continue

            # Check which phase we are in currently
            self.curr_phase = self.characterizer.get_current_phase()

            # Based on the current phase make a prediction
            predicted, phase_exists = self.predictor.get_prediction(self.curr_phase)
            print(predicted)
            # Log data for error calculation and print predictions
            if ENABLE_STATS:
                stats["predicted_data"].append(predicted)
                stats["actual_data"].append(self.database.get_curr_resource())
                self.calculate_errors()

            logging.info("Actual: " + str(["{:.2f}".format(a) for a in self.database.get_curr_resource()]) + " Predicted:" + str(["{:.2f}".format(a) for a in predicted]))
            anomaly_detected = self.predictor.detect_anomaly(predicted, self.database.get_curr_resource(), self.curr_phase, phase_exists)
            if anomaly_detected == True:
                self.sawcap_exit()
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
    def sawcap_exit(self, signal_received = None, frame = None):
        self.calculate_errors()
        logging.info('\nExiting after saving the current database')
        self.database.save_database(self.datadir, self.algo)
        sys.exit(2)

    def calculate_errors(self):
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
    datadir = "/home/ubuntu/data"
    algo = "lasso"
    sawcap = Sawcap(datadir, algo)
    sawcap.run()
