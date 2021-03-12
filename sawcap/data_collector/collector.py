import os
import requests
from config import DATA_DIR, NUM_RESOURCES, LOCAL_DATA_DIR, WORKER_DATA_API_PORT
import logging


class DataCollector:

    def __init__(self, workers):
        self.workers = workers
        self.prev_resource_values = [[0.0 for _ in range(NUM_RESOURCES)] for _ in range(len(workers))]

    def _parse_resource_agg(self, resource_agg):
        num_resources = NUM_RESOURCES
        resource_usage = [0] * num_resources

        for line in resource_agg:
            usages = line.split(',')
            for i in range(num_resources):
                # Handle case where line has issues either something like cpu,  or cpu,mem,bogus
                if usages[i] == "" or len(usages) != num_resources:
                    # Use previous value of the resource value for the worker
                    resource_usage[i] += self.prev_resource_values[worker_index][i]
                    logging.error(f"line has an issue, using previous value, here is the problematic line: {line}")
                else:
                    try:
                        resource_usage[i] += float(usages[i])
                        self.prev_resource_values[worker_index][i] = float(usages[i])
                    except ValueError:
                        # Handle any float conversion errors
                        resource_usage[i] += self.prev_resource_values[worker_index][i]
                        logging.error(f"line has an issue, using previous value, here is the problematic line: {line}")

        resource_usage = [float(i) / len(self.workers) for i in resource_usage]

        return resource_usage

    def get_data_from_workers(self):
        # this function connects to the servers, fetches the threaddump, aggregates
        # them and extract threaddump and resource usage information from them
        # returns a list containing the threaddump and resource info

        threaddump_agg = []
        resource_agg = []

        # fetch new data
        for s in self.workers:
            worker_data_response = requests.get(f"http://{s}:{WORKER_DATA_API_PORT}/worker_data")

            # All workers should be able to send data, if not raise an Error
            if worker_data_response.status_code != 200:
                logging.error(f"Error collecting data from worker: {s}")
                raise ConnectionError(f"Could not connect to worker: {s}")
            else:
                worker_data = worker_data_response.json()
                threaddump_agg.extend(worker_data["threaddump_data"])
                resource_agg.append(worker_data["resource_data"])

        resource_agg = self._parse_resource_agg(resource_agg)
        functions = [i.strip() for i in threaddump_agg]
        functions = [i.split("***")[0] for i in functions]

        return set(functions), resource_agg
