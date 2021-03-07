import os

from config import DATA_DIR, NUM_RESOURCES, LOCAL_DATA_DIR
import logging


class DataCollector:

    def __init__(self, workers):
        self.workers = workers
        self.prev_resource_values = [[0.0 for _ in range(NUM_RESOURCES)] for _ in range(len(workers))]

    def _parse_resource_agg(self, file):
        # takes an input file which has one line per server for CPU and Mem
        # returns an aggregate of three
        lines = []
        with open(file) as f:
            lines = f.readlines()

        num_resources = NUM_RESOURCES
        resource_usage = [0] * num_resources

        for worker_index, line in enumerate(lines):
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

        # clear the prev buffer
        os.system(f"> {LOCAL_DATA_DIR}/threaddump_agg")
        os.system(f"> {LOCAL_DATA_DIR}/resource_agg")

        # fetch new data
        for s in self.workers:
            # accumulate threaddumps
            # When anomaly is run in any of the slaves, ssh also takes longer, so the timeout heuristics
            # is simple but powerful to detect those anomalies, though the timeout value should change
            # system to system
            command = "timeout --foreground 2 ssh -q -t " + s + f" 'cat {DATA_DIR}/threaddump_data' " \
                                                                f">> {LOCAL_DATA_DIR}/threaddump_agg"
            os.system(command)
            # accumulate resource usage
            command = "timeout --foreground 2 ssh -q -t " + s + f" 'cat {DATA_DIR}/resource_data' " \
                                                                f">> {LOCAL_DATA_DIR}/resource_agg"
            os.system(command)

        functions = []

        with open(f"{LOCAL_DATA_DIR}/threaddump_agg") as f:
            functions = f.readlines()

        resource_agg = self._parse_resource_agg(f"{LOCAL_DATA_DIR}/resource_agg")
        functions = [i.strip() for i in functions]
        functions = [i.split("***")[0] for i in functions]

        return set(functions), resource_agg
