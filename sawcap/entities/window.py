from data_aggregator.data_aggregator import DataAggregator
import math

# Class for representing a window entity
class Window:
    def __init__(self, window_size, resource_data, stacktrace_data):
        self.window_size = window_size
        self.resource_data = resource_data
        self.stacktrace_data = stacktrace_data
        self.resource_aggregation = [] # Will replace with a function call in DataAggregator later

        data_aggregator = DataAggregator(self)
        self.unique_stacktraces, self.thread_histograms = data_aggregator.generate_histograms_and_unique_stacktraces()

    # the current window is treated as the reference point
    def stacktrace_similarity(self, other_window):
        common_stacktraces = set(self.unique_stacktraces).intersection(other_window.unique_stacktraces)
        return len(common_stacktraces) / len(self.unique_stacktraces)

    def threadcount_similarity(self, other_window):
        common_stacktraces = set(self.unique_stacktraces).intersection(other_window.unique_stacktraces)
        common_thread_histogram_current = []
        common_thread_histogram_other = []

        for index, stacktrace in enumerate(self.unique_stacktraces):
            if stacktrace in common_stacktraces:
                common_thread_histogram_current.append(self.thread_histograms[index])

        for index, stacktrace in enumerate(other_window.unique_stacktraces):
            if stacktrace in common_stacktraces:
                common_thread_histogram_other.append(other_window.thread_histograms[index])
        
        assert(len(common_thread_histogram_current) == len(common_thread_histogram_other))

        threadcount_similarity = 0

        for h_curr, h_other in zip(common_thread_histogram_current, common_thread_histogram_other):
            # Squared-Chord Distance
            threadcount_similarity += ((math.sqrt(h_curr) - math.sqrt(h_other)) ** 2)
        
        return threadcount_similarity
