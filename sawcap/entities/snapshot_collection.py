from data_aggregator import data_aggregator
import math
import numpy as np

# Class for representing a snapshot_collection entity
class SnapshotCollection:
    # Inputs:
    #   window_size: length of the window i.e number of snapshots in the collection, type: int
    #   resource_data: list of strings with each string being comma seperated values, type: list (of strings)
    #   stacktrace_data: list of strings with each string being the aggregate stacktrace, type: list (of strings)

    def __init__(self, window_size, raw_resource_data, stacktrace_data):
        assert(len(raw_resource_data) == len(stacktrace_data))
        assert(len(raw_resource_data) == window_size)
        assert(window_size > 0)

        self.window_size = window_size
        self.resource_data = self._format_resource_data(raw_resource_data)
        self.stacktrace_data = stacktrace_data
        self.resource_aggregation = data_aggregator.generate_resource_aggregation(
            self.resource_data)

        self.unique_stacktraces, self.thread_histograms = data_aggregator.generate_histograms_and_unique_stacktraces(
            self.stacktrace_data)

    # the current snapshot_collection is treated as the reference point
    def stacktrace_similarity(self, other_snapshot_collection):
        common_stacktraces = set(self.unique_stacktraces).intersection(
            other_snapshot_collection.unique_stacktraces)
        assert(len(self.unique_stacktraces) != 0)
        return len(common_stacktraces) / len(self.unique_stacktraces)

    def threadcount_similarity(self, other_snapshot_collection):
        common_stacktraces = set(self.unique_stacktraces).intersection(
            other_snapshot_collection.unique_stacktraces)
        common_thread_histogram_current = []
        common_thread_histogram_other = []

        for index, stacktrace in enumerate(self.unique_stacktraces):
            if stacktrace in common_stacktraces:
                common_thread_histogram_current.append(
                    self.thread_histograms[index])

        for index, stacktrace in enumerate(other_snapshot_collection.unique_stacktraces):
            if stacktrace in common_stacktraces:
                common_thread_histogram_other.append(
                    other_snapshot_collection.thread_histograms[index])

        assert(len(common_thread_histogram_current)
               == len(common_thread_histogram_other))

        threadcount_similarity = 0

        for h_curr, h_other in zip(common_thread_histogram_current, common_thread_histogram_other):
            # Squared-Chord Distance
            threadcount_similarity += ((math.sqrt(h_curr) -
                                        math.sqrt(h_other)) ** 2)

        return threadcount_similarity

    def _format_resource_data(self, raw_resource_data):
        num_resources = len(raw_resource_data[0])
        resources = [list() for _ in range(num_resources)]

        for sample in raw_resource_data:
            for i, resource_metric in enumerate(sample):
                if resource_metric == '':
                    # THIS IS NOT FINE, SHOULD ADD BETTER LOGIC
                    resources[i].append(0)
                else:
                    resources[i].append(float(resource_metric))
        for i, resource in enumerate(resources):
            resources[i] = np.array(resource)

        return resources
