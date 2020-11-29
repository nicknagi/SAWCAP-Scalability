from data_aggregator import data_aggregator
import math

# Class for representing a snapshot_collection entity
class SnapshotCollection:
    def __init__(self, snapshot_collection_size, resource_data, stacktrace_data):
        self.window_size = snapshot_collection_size
        self.resource_data = resource_data
        self.stacktrace_data = stacktrace_data
        self.resource_aggregation = [] # TODO: Implement the functionality

        self.unique_stacktraces, self.thread_histograms = data_aggregator.generate_histograms_and_unique_stacktraces(self.stacktrace_data)

    # the current snapshot_collection is treated as the reference point
    def stacktrace_similarity(self, other_snapshot_collection):
        common_stacktraces = set(self.unique_stacktraces).intersection(other_snapshot_collection.unique_stacktraces)
        assert(len(self.unique_stacktraces) != 0)
        return len(common_stacktraces) / len(self.unique_stacktraces)

    def threadcount_similarity(self, other_snapshot_collection):
        common_stacktraces = set(self.unique_stacktraces).intersection(other_snapshot_collection.unique_stacktraces)
        common_thread_histogram_current = []
        common_thread_histogram_other = []

        for index, stacktrace in enumerate(self.unique_stacktraces):
            if stacktrace in common_stacktraces:
                common_thread_histogram_current.append(self.thread_histograms[index])

        for index, stacktrace in enumerate(other_snapshot_collection.unique_stacktraces):
            if stacktrace in common_stacktraces:
                common_thread_histogram_other.append(other_snapshot_collection.thread_histograms[index])
        
        assert(len(common_thread_histogram_current) == len(common_thread_histogram_other))

        threadcount_similarity = 0

        for h_curr, h_other in zip(common_thread_histogram_current, common_thread_histogram_other):
            # Squared-Chord Distance
            threadcount_similarity += ((math.sqrt(h_curr) - math.sqrt(h_other)) ** 2)
        
        return threadcount_similarity
