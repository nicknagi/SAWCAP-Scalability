import numpy as np
from scipy.stats import kurtosis, skew
import pmdarima as pm

# Input: stacktrace_data is a list of aggregate_stacktraces of len window_size
def generate_histograms_and_unique_stacktraces(stacktrace_data):
    histograms = _build_histogram(stacktrace_data)

    unique_stacktraces = list(histograms.keys())
    thread_histograms = list(histograms.values())

    return unique_stacktraces, thread_histograms

def generate_resource_aggregation(resource_data):
    aggregation = []
    assert(isinstance(wavelet, np.ndarray) for wavelet in resource_data)
    for wavelet in resource_data:
        minimum = wavelet.min()
        maximum = wavelet.max()
        mean = wavelet.mean()
        standard_deviation = np.std(wavelet)
        skewness = skew(wavelet)
        kurt = kurtosis(wavelet)
        p, d, q = pm.auto_arima(wavelet, njobs=-1, suppress_warnings=True).order
        aggregation.append([minimum, maximum, mean, standard_deviation, skewness, kurt, p, d, q])
    return aggregation

def _build_histogram(stacktrace_data):
    histograms = {}
    for stacktrace_dump in stacktrace_data:
        functions, counts = _extract_functions_and_counts(stacktrace_dump)
        assert(len(functions) == len(counts))

        for function, freq in zip(functions, counts):
            if function in histograms:
                # Might not want to do this as over multiple dumps this value will add up [will take care of this later]
                histograms[function] += freq
            else:
                histograms[function] = freq
    return histograms

def _extract_functions_and_counts(stacktrace):
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
