from data_aggregator.data_aggregator import DataAggregator

# Class for representing a snapshot entity
class Snapshot:
    def __init__(self, window_size, resource_data, stacktrace_data):
        self.window_size = window_size
        self.resource_data = resource_data
        self.stacktrace_data = stacktrace_data
        self.resource_aggregation = [] # Will replace with a function call in DataAggregator later

        data_aggregator = DataAggregator(self)
        self.stacktrace_aggregation = data_aggregator.generate_histograms_and_unique_stacktraces()

    def stacktrace_similarity(self, other_snapshot):
        pass

    def threadcount_similarity(self, other_snapshot):
        pass
