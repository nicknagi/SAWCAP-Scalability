# Class for representing a snapshot entity
class Snapshot:
    # Inputs:
    #   resource_data: list of floats representing resource usages -- cpu, mem etc., type: list (of floats)
    #   stacktrace_data: list of strings representing individual functions in stacktrace, type: set (of strings)

    def __init__(self, raw_resource_data, stacktrace_data):
        self.resource_data = raw_resource_data
        self.stacktrace_data = stacktrace_data

    # the current snapshot_collection is treated as the reference point
    def stacktrace_similarity(self, other_snapshot_collection):
        common_stacktraces = self.stacktrace_data.intersection(
            other_snapshot_collection.stacktrace_data)

        divisor = max(len(self.stacktrace_data), len(
            other_snapshot_collection.stacktrace_data))
        assert (divisor != 0)
        similarity = len(common_stacktraces) / float(divisor)

        return similarity
