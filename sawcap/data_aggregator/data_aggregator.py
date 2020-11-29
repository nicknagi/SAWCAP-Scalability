import os

class DataAggregator:
    '''
    input_data: {resource_usage: [[1,2], [10,11] ...], stacktraces: [A, B, C, D...]} # Should be changed to a window object later on
    input_data is essentially the snapshot that we need to aggregate
    '''

    def __init__(self, window):
        self._window = window

    def generate_histograms_and_unique_stacktraces(self):
        histograms = self._build_histogram(self._window.stacktrace_data)

        unique_stacktraces = list(histograms.keys())
        thread_histograms = list(histograms.values())

        return unique_stacktraces, thread_histograms

    def _build_histogram(self, stacktrace_data):
        histograms = {}
        for stacktrace_dump in stacktrace_data:
            functions, counts = self._extract_functions_and_counts(stacktrace_dump)
            assert(len(functions) == len(counts))

            for function, freq in zip(functions, counts):
                if function in histograms:
                    # Might not want to do this as over multiple dumps this value will add up [will take care of this later]
                    histograms[function] += freq
                else:
                    histograms[function] = freq
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
