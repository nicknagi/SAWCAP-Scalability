from influxdb import InfluxDBClient
import logging
from config import ORCHESTRATOR_PRIVATE_IP
import socket

class MetricsPublisher:
    def __init__(self):
        self.client = None
        try:
            self.client = InfluxDBClient(ORCHESTRATOR_PRIVATE_IP, 8086, 'metrics')
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
                    "actual_cpu": actual[0],
                    "actual_mem": actual[1],
                    "predicted_cpu": predicted[0],
                    "predicted_mem": predicted[1]
                }
            }
        ]
        self.client.write_points(json_body)


