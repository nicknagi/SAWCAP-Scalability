import functools
import time

from metrics.metrics_publisher import MetricsPublisher


def publish_latency(measurement_name):
    def metrics_decorator(func):
        @functools.wraps(func)
        def run_and_time_func(*args, **kwargs):
            start = time.time()
            func(*args, **kwargs)
            end = time.time()
            MetricsPublisher().publish_arbitrary_metrics({"latency": end-start}, measurement_name)

        return run_and_time_func

    return metrics_decorator
