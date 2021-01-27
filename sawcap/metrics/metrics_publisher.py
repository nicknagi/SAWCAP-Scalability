from influxdb import InfluxDBClient
import logging
from config import ORCHESTRATOR_PRIVATE_IP
import socket

class MetricsPublisher:
    def __init__(self):
        self.client = None
        try:
            self.client = InfluxDBClient(ORCHESTRATOR_PRIVATE_IP, 8086, database='metrics')
            self.client.create_database('metrics')
            self.hostname = str(socket.getfqdn())
        except Exception as e:
            logging.error(f"There was a problem connecting to InfluxDB at IP {ORCHESTRATOR_PRIVATE_IP} {e}")
            logging.info("Will not publish statistics")
    
    # Args are lists with 2 elements each -- cpu and mem
    def publish_predictions(self, actual, predicted):
        json_body = [
            {
                "measurement": "predictions",
                "tags": {
                    "host": self.hostname
                },
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
        json_body = [
            {
                "measurement": "accuracy",
                "tags": {
                    "host": self.hostname
                },
                "fields": {
                    "acc_cpu": float(acc_cpu),
                    "acc_mem": float(acc_mem)
                }
            }
        ]
        self.client.write_points(json_body)


