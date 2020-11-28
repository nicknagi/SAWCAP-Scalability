import os

'''
For each stacktrace build a set of threads being executed and a corresponding histogram (function -> num thread running)
Then build functions for calculating stacktrace and threadcount similarity between two associated inputs as described in the paper
'''

class DataAggregator:
    '''
    input_data: {resource_usage: [[1,2], [10,11] ...], stacktraces: [A, B, C, D...]} # Should be changed to a snapshot object later on
    input_data is essentially the snapshot that we need to aggregate
    '''

    def __init__(self):
        self._histograms = []

    def aggregate(self, snapshot):
        self._histograms = self._build_histogram(snapshot.stacktrace_data)
        # Call sub-functions to calculate the individual metrics

        # Returns a vector (list) that is an aggregation of the snapshot
        pass

    def _build_histogram(self, stacktrace_data):
        histograms = []
        for stacktrace in stacktrace_data:
            functions, counts = self._extract_functions_and_counts(stacktrace)
            assert(len(functions) == len(counts))

            histogram_entry = {}
            for function, freq in zip(functions, counts):
                histogram_entry[function] = freq
            histograms.append(histogram_entry)
        return histograms

    def _extract_functions_and_counts(self, stacktrace):
        stacktrace_chunks = stacktrace.split('\n\n')[1:] # find all the empty lines and split
        stacks = []
        counts = []

        for chunk in stacktrace_chunks:
            if "Stack:\n" not in chunk:
                continue
            stack = chunk.split("Stack:\n")[1]
            if "spark" in stack:
                counts.append(int(chunk.split("States:")[0].split(" ")[0]))
                stacks.append(stack)

        return stacks, counts