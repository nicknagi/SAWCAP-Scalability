import requests
from config import NUM_RESOURCES, WORKER_DATA_API_PORT
import logging
import multiprocessing as mp
import signal


def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)


def get_data_from_worker(worker_address):
    try:
        worker_data_response = requests.get(f"http://{worker_address}:{WORKER_DATA_API_PORT}/worker_data", timeout=2)
    except requests.Timeout:
        logging.error(f"Request to {worker_address} took too long, timing out and returning")
        return {"threaddump_data": [""], "resource_data": "0,0"}
    if worker_data_response.status_code != 200:
        logging.error(f"Error collecting data from worker: {worker_address}")
        raise ConnectionError(f"Could not connect to worker: {worker_address}")
    else:
        worker_data = worker_data_response.json()
        return worker_data


def get_data_in_parallel(workers):
    with mp.Pool(min(int(len(workers) / 5), 10), init_worker) as pool:
        worker_data_json = pool.map(get_data_from_worker, workers)
        return worker_data_json


class DataCollector:

    def __init__(self, workers):
        self.workers = workers
        self.prev_resource_values = [[0.0 for _ in range(NUM_RESOURCES)] for _ in range(len(workers))]

    def _parse_resource_agg(self, resource_agg):
        num_resources = NUM_RESOURCES
        resource_usage = [0] * num_resources

        for worker_index, line in enumerate(resource_agg):
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
        threaddump_agg = []
        resource_agg = []
        if len(self.workers) >= 10:
            worker_data_json = get_data_in_parallel(self.workers)
        else:
            worker_data_json = []
            for worker in self.workers:
                worker_data_json.append(get_data_from_worker(worker))

        for data in worker_data_json:
            threaddump_agg.extend(data["threaddump_data"])
            resource_agg.append(data["resource_data"])

        resource_agg = self._parse_resource_agg(resource_agg)
        functions = [i.strip() for i in threaddump_agg]
        functions = [i.split("***")[0] for i in functions]

        return set(functions), resource_agg
