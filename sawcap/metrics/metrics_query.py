import logging
import socket
import argparse
from influxdb import InfluxDBClient
from datetime import datetime, timezone

class MetricsQuery:
    def __init__(self):
        self.client = None
        self.id_lookup = {
            "baseline-test": ["2021-02-23T22:00:00Z", "2021-02-23T22:59:00Z"],
            "ten-node-test": ["2021-02-23T22:15:00Z", "2021-02-23T22:53:00Z"],
            "twenty-five-node-test": ["2021-03-04T19:39:00Z", "2021-03-04T20:19:00Z"],
            "fifty-node-test": ["2021-03-04T21:23:00Z", "2021-03-04T21:55:00Z"],
            "nn-test": ["2021-03-07T03:00:00Z", "2021-03-07T03:10:00Z"],
        }
        try:
            self.client = InfluxDBClient( "192.168.0.3", 8086, database='metrics')
            self.client.create_database('metrics')
            self.hostname = str(socket.getfqdn())
        except Exception as e:
            logging.error(f"There was a problem connecting to InfluxDB at IP {ORCHESTRATOR_PRIVATE_IP} {e}")
            logging.info("Will not publish statistics")

    def to_date(self, date):
        return self.utc_to_local(datetime.strptime(date,'%Y-%m-%dT%H:%M:%SZ'))

    def utc_to_local(self, utc_dt):
        return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)

    def get_max_val(self, id, metric):
        """
           id: uniqueId of experiment
           metric: metric to look for (eg. 'cpu')
        """
        if id in self.id_lookup.keys():
            experiment = self.id_lookup[id]
        else:
            logging.error(f"Unique id '{id}' not found")
            return
        t_start = experiment[0]
        t_end = experiment[1]
        print(f"start: {self.to_date(t_start)}, end: {self.to_date(t_end)}")

        select_query = f'SELECT MAX("{metric}") from "sawcap_resource_consumption" WHERE time >= \'{t_start}\' AND time < \'{t_end}\';'
        result = self.client.query(select_query)
        data_points = list(result.get_points(measurement='sawcap_resource_consumption'))
        print(f"Max {metric} for {id}: {data_points[0]['max']}")

    def get_min_val(self, id, metric):
        """
           id: uniqueId of experiment
           metric: metric to look for (eg. 'cpu')
        """
        if id in self.id_lookup.keys():
            experiment = self.id_lookup[id]
        else:
            logging.error(f"Unique id '{id}' not found")
            return
        t_start = experiment[0]
        t_end = experiment[1]
        print(f"start: {self.to_date(t_start)}, end: {self.to_date(t_end)}")

        select_query = f'SELECT MIN("{metric}") from "sawcap_resource_consumption" WHERE time >= \'{t_start}\' AND time < \'{t_end}\';'
        result = self.client.query(select_query)
        data_points = list(result.get_points(measurement='sawcap_resource_consumption'))
        print(f"Min {metric} for {id}: {data_points[0]['min']}")

    def get_avg_vals(self, id, metric):
        """ Group averages by 5min intervals
           id: uniqueId of experiment
           metric: metric to look for (eg. 'cpu')
        """
        if id in self.id_lookup.keys():
            experiment = self.id_lookup[id]
        else:
            logging.error(f"Unique id '{id}' not found")
            return
        t_start = experiment[0]
        t_end = experiment[1]
        print(f"start: {self.to_date(t_start)}, end: {self.to_date(t_end)}")

        select_query = f'SELECT MEAN("{metric}") from "sawcap_resource_consumption" WHERE (time >= \'{t_start}\' AND time < \'{t_end}\') GROUP BY time(5m);'
        result = self.client.query(select_query)
        data_points = list(result.get_points(measurement='sawcap_resource_consumption'))
        for entry in data_points:
            print(f"{self.to_date(entry['time'])}: {entry['mean']:.5f}")

parser = argparse.ArgumentParser()
parser.add_argument("-uid", "--uniqueid", help="Unique Id of experiment")
parser.add_argument("-m", "--metric", help="Metric to look for cpu, mem, download, upload etc.")
parser.add_argument("-op", "--operation", help="Operation to perform max, min, avg etc.")
args = parser.parse_args()

metrics_query = MetricsQuery()

if args.operation == 'max':
    metrics_query.get_max_val(args.uniqueid, args.metric)
elif args.operation == 'min':
    metrics_query.get_min_val(args.uniqueid, args.metric)
elif args.operation == 'avg':
    metrics_query.get_avg_vals(args.uniqueid, args.metric)
else:
    logging.error(f"Invalid input")