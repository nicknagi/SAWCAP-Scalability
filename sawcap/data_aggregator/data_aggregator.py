import os

class DataAggregator:
    '''
    input_data: {resource_usage: [[1,2], [10,11] ...], stacktraces: [A, B, C, D...]} # Should be changed to a snapshot object later on
    input_data is essentially the snapshot that we need to aggregate
    '''

    def __init__(self, snapshot):
        self._snapshot = snapshot

    def generate_histograms_and_unique_stacktraces(self):
        histograms = self._build_histogram(self._snapshot.stacktrace_data)
        stacktrace_histogram_pairs = []

        for histogram in histograms:
            stacktrace_histogram_pairs.append(
                [list(histogram.keys()), histogram])

        return stacktrace_histogram_pairs

    def _build_histogram(self, stacktrace_data):
        histograms = []
        for stacktrace in stacktrace_data:
            functions, counts = self._extract_functions_and_counts(stacktrace)
            assert(len(functions) == len(counts))

            histogram_entry = {}
            for function, freq in zip(functions, counts):
                if function in histogram_entry:
                    histogram_entry[function] += freq
                else:
                    histogram_entry[function] = freq
            histograms.append(histogram_entry)
        return histograms

    def _extract_functions_and_counts(self, stacktrace):
        # find all the empty lines and split
        stacktrace_chunks = stacktrace.split('\n\n')[1:]
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
