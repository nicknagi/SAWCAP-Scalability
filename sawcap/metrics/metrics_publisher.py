import logging
import socket

import numpy as np
from influxdb import InfluxDBClient

from config import ORCHESTRATOR_PRIVATE_IP, EXPERIMENT_NAME


class MetricsPublisher:
    def __init__(self):
        self.client = None
        try:
            self.client = InfluxDBClient(ORCHESTRATOR_PRIVATE_IP, 8086, database='metrics')
            self.client.create_database('metrics')
            self.hostname = str(socket.getfqdn())
            self.tags = {
                    "host": self.hostname,
                    "experiment_name": EXPERIMENT_NAME
                }

        except Exception as e:
            logging.error(f"There was a problem connecting to InfluxDB at IP {ORCHESTRATOR_PRIVATE_IP} {e}")
            logging.info("Will not publish statistics")

    # Args are lists with 2 elements each -- cpu and mem
    def publish_predictions(self, actual, predicted):
        json_body = [
            {
                "measurement": "predictions",
                "tags": self.tags,
                "fields": {
                    "actual_cpu": float(actual[0]),
                    "actual_mem": float(actual[1]),
                    "predicted_cpu": float(predicted[0]),
                    "predicted_mem": float(predicted[1])
                }
            }
        ]
        self.client.write_points(json_body)

    # Args are floats with accuracies -- cpu and mem
    def publish_accuracy(self, acc_cpu, acc_mem):
        if np.isnan(acc_cpu):
            return
        json_body = [
            {
                "measurement": "accuracy",
                "tags": self.tags,
                "fields": {
                    "acc_cpu": float(acc_cpu),
                    "acc_mem": float(acc_mem)
                }
            }
        ]
        self.client.write_points(json_body)

    # fields_data - dict with data to be inserted into <measurement>
    def publish_arbitrary_metrics(self, fields_data, measurement):
        json_body = [
            {
                "measurement": measurement,
                "tags": self.tags,
                "fields": fields_data
            }
        ]
        self.client.write_points(json_body)
