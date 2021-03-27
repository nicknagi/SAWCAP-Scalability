import logging
import socket
import argparse
import sys
import statistics as stat
from influxdb import InfluxDBClient
from datetime import datetime, timezone

class MetricsQuery:
    def __init__(self):
        self.client = None
        try:
            self.client = InfluxDBClient("192.168.0.3", 8086, database='metrics')
            self.client.create_database('metrics')
            self.hostname = str(socket.getfqdn())
        except Exception as e:
            logging.error(f"There was a problem connecting to InfluxDB at IP {ORCHESTRATOR_PRIVATE_IP} {e}")
            logging.info("Will not publish statistics")

    def to_date(self, date):
        return self.utc_to_local(datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ'))

    def utc_to_local(self, utc_dt):
        return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)

    def full_report(self, id, name):
        file = f'{id}_{name}_full_test_report.txt'
        with open(file, 'w') as f:
            sys.stdout = f

            print(f"\n### Sawcap Resource Usage Stats for {id}: {name} ##")
            print(f"\n  MAX")
            self.get_max_val(id, 'cpu', name)
            self.get_max_val(id, 'mem', name)
            self.get_max_val(id, 'download', name)
            self.get_max_val(id, 'upload', name)

            print(f"\n  MIN")
            self.get_min_val(id, 'cpu', name)
            self.get_min_val(id, 'mem', name)
            self.get_min_val(id, 'download', name)
            self.get_min_val(id, 'upload', name)

            print(f"\n### Prediction Stats ###\n")
            self.get_prediction_frequency(id)

            print(f"\n  AVERAGE")
            self.get_avg_resources(id, 'cpu', name)
            self.get_avg_resources(id, 'mem', name)
            self.get_avg_resources(id, 'download', name)
            self.get_avg_resources(id, 'upload', name)

            print(f"\n  AVERAGE")
            self.get_avg_predictions(id, 'actual_cpu', name)
            self.get_avg_predictions(id, 'predicted_cpu', name)
            self.get_avg_predictions(id, 'actual_mem', name)
            self.get_avg_predictions(id, 'predicted_mem', name)

            print(f"\n### Latency Stats ###\n")
            self.get_latency_metrics(args.uniqueid, 'data_collection_latency', name)
            self.get_latency_metrics(args.uniqueid, 'prediction_latency', name)
            self.get_latency_metrics(args.uniqueid, 'ml_model_update_latency', name)
            self.get_latency_metrics(args.uniqueid, 'anomaly_detection_latency', name)

    def get_max_val(self, id, metric, name):
        """
           id: uniqueId of experiment
           metric: metric to look for (eg. 'cpu')
        """

        select_query = f'SELECT MAX("{metric}") from "sawcap_resource_consumption" WHERE host=\'runner-{id}\'' \
                       f' and experiment_name=\'{name}\';'
        result = self.client.query(select_query)
        data_points = list(result.get_points(measurement='sawcap_resource_consumption'))
        print(f"Max {metric} for {id}: {data_points[0]['max']:.5f}")

    def get_min_val(self, id, metric, name):
        """
           id: uniqueId of experiment
           metric: metric to look for (eg. 'cpu')
        """

        select_query = f'SELECT MIN("{metric}") from "sawcap_resource_consumption" WHERE host=\'runner-{id}\'' \
                       f' and experiment_name=\'{name}\';'
        result = self.client.query(select_query)
        data_points = list(result.get_points(measurement='sawcap_resource_consumption'))
        print(f"Min {metric} for {id}: {data_points[0]['min']:.5f}")

    def get_avg_resources(self, id, metric, name):
        """ Group averages by 5min intervals
           id: uniqueId of experiment
           metric: metric to look for (eg. 'cpu')
        """

        # average per 5 min
        select_query = f'SELECT MEAN("{metric}") from "sawcap_resource_consumption" WHERE host=\'runner-{id}\'' \
                       f' and experiment_name=\'{name}\' GROUP BY time(5m);'
        result = self.client.query(select_query)
        data_points = list(result.get_points(measurement='sawcap_resource_consumption'))
        print(f"  Average {metric} for {id} per 5 minutes")
        data = []
        for entry in data_points:
            if entry['mean']:
                data.append(entry['mean'])
                print(f"{self.to_date(entry['time'])}: {entry['mean']:.5f}")
        mean = stat.mean(data)
        print(mean)
        print("")

    def get_avg_predictions(self, id, metric, name):
        """ Group averages by 5min intervals
           id: uniqueId of experiment
           metric: metric to look for (eg. 'cpu')
        """

        # average per 5 min
        select_query = f'SELECT MEAN("{metric}") from "predictions" WHERE host=\'runner-{id}\'' \
                       f' and experiment_name=\'{name}\' GROUP BY time(5m);'
        result = self.client.query(select_query)
        data_points = list(result.get_points(measurement='predictions'))
        print(f"  Average {metric} for {id} per 5 minutes")
        data = []
        for entry in data_points:
            if entry['mean']:
                data.append(entry['mean'])
                print(f"{self.to_date(entry['time'])}: {entry['mean']:.5f}")
        mean = stat.mean(data)
        print(mean)
        print("")

    def get_prediction_frequency(self, id):
        """ Get the frequency that sawcap makes cpu and mem predictions
           id: uniqueId of experiment
        """

        select_query_cpu_pred = f'SELECT COUNT("predicted_cpu") from "predictions" WHERE host=\'runner-{id}\'' \
                                f' and experiment_name=\'{args.experiment_name}\';'
        result = self.client.query(select_query_cpu_pred)
        data_points = list(result.get_points(measurement='predictions'))
        print(f"Number of cpu predictions for {id}: {data_points[0]['count']}")

        select_query_mem_pred = f'SELECT COUNT("predicted_mem") from "predictions" WHERE host=\'runner-{id}\'' \
                                f' and experiment_name=\'{args.experiment_name}\';'
        result = self.client.query(select_query_mem_pred)
        data_points = list(result.get_points(measurement='predictions'))
        print(f"Number of mem predictions for {id}: {data_points[0]['count']}")

    def get_latency_metrics(self, id, metric, name):
        """ Get the latency of sawcap metrics
           id: uniqueId of experiment
        """

        # average per 5 min
        select_query = f'SELECT MEAN("latency") from "{metric}" WHERE host=\'runner-{id}\'' \
                       f' and experiment_name=\'{name}\' GROUP BY time(5m);'
        result = self.client.query(select_query)
        data_points = list(result.get_points(measurement=metric))
        print(f"  Average {metric} (seconds) for {id} per 5 minutes")
        data = []
        for entry in data_points:
            if entry['mean']:
                data.append(entry['mean'])
                print(f"{self.to_date(entry['time'])}: {entry['mean']:.5f}")
        mean = stat.mean(data)
        print(mean)
        print("")

    def test(self, id):
        select_query = f"SELECT * from \"sawcap_resource_consumption\" WHERE host='runner-{id}'" \
                       f" and experiment_name='{args.experiment_name}';"
        result = self.client.query(select_query)
        data_points = list(result.get_points(measurement='sawcap_resource_consumption'))
        print(f"Max cpu for {id}: {data_points[0]['max']:.5f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-uid", "--uniqueid", help="Unique Id of experiment")
    parser.add_argument("-m", "--metric", help="Metric to look for cpu, mem, download, upload etc.")
    parser.add_argument("-op", "--operation", help="Operation to perform max, min, avg, freq, latency etc.")
    parser.add_argument("--all", help="Generate full report", default=False, action='store_true')
    parser.add_argument("-name", "--experiment_name", help="Name of the experiment to generate report for")
    parser.add_argument("--test", help="Testing flag", default=False, action='store_true')
    args = parser.parse_args()

    metrics_query = MetricsQuery()

    original_stdout = sys.stdout

    if args.test:
        metrics_query.test(args.uniqueid)
        exit()

    if args.all and args.experiment_name:
        metrics_query.full_report(args.uniqueid, args.experiment_name)
        sys.stdout = original_stdout
        exit()

    if args.operation == 'max':
        metrics_query.get_max_val(args.uniqueid, args.metric)
    elif args.operation == 'min':
        metrics_query.get_min_val(args.uniqueid, args.metric)
    elif args.operation == 'avg':
        metrics_query.get_avg_resources(args.uniqueid, args.metric)
    elif args.operation == 'freq':
        metrics_query.get_prediction_frequency(args.uniqueid)
    elif args.operation == 'latency':
        metrics_query.get_latency_metrics(args.uniqueid, args.metric)
    else:
        logging.error(f"Invalid input")