import unittest
from data_aggregator import data_aggregator
from scipy.stats import truncnorm, kurtosis, skew

class TestDataAggregator(unittest.TestCase):

    # Will replace this function with DataCollector class methods later
    def _generate_stacktrace_data_helper(self, filename):
        with open("data_aggregator/tests/sample_data/"+filename, "r") as f:
            # Return a snapshot_collection with snapshot_collection size 1
            return [f.read()]
    
    def _get_truncated_normal(self, mean=0, sd=1, low=0, upp=10):
        return truncnorm(
            (low - mean) / sd, (upp - mean) / sd, loc=mean, scale=sd)

    def _generate_resource_data_helper(self):
        return [self._get_truncated_normal(16, 4, 1, 24).rvs(1000), self._get_truncated_normal(32, 32, 4, 128).rvs(1000)]

    def test_generate_histograms_and_unique_stacktraces_function_no_duplicates(self):
        stacktrace_data = self._generate_stacktrace_data_helper("threaddump_aggregate_simple")

        actual_data = data_aggregator.generate_histograms_and_unique_stacktraces(stacktrace_data)
        expected_data = ([" - org.apache.spark.executor.CoarseGrainedExecutorBackend.main(CoarseGrainedExecutorBackend.scala)"], [1])
        self.assertEqual(actual_data, expected_data)

    def test_generate_histograms_and_unique_stacktraces_function_duplicates(self):
        stacktrace_data = self._generate_stacktrace_data_helper("threaddump_aggregate_duplicate")

        actual_data = data_aggregator.generate_histograms_and_unique_stacktraces(stacktrace_data)
        expected_data = ([" - org.apache.spark.executor.CoarseGrainedExecutorBackend.main(CoarseGrainedExecutorBackend.scala)"], [3])
        self.assertEqual(actual_data, expected_data)

    # Hard to test statistics related function, this testcase only checks the simple ones
    def test_generate_resource_aggregation(self):
        generated_resource_data = self._generate_resource_data_helper()
        # Format: min, max, avg, std, skew, kurt, p, d, q -- setting some to 0 for now as not implemented
        expected_stats = [[1,24,16,4,0,0,0,0,0], [4, 128, 32, 32,0,0,0,0,0]]
        actual_stats = data_aggregator.generate_resource_aggregation(generated_resource_data)

        # For each wavelet ensure conditions
        for i in range(len(expected_stats)):
            self.assertTrue(actual_stats[i][0] >= expected_stats[i][0]) # check minimum bound
            self.assertTrue(actual_stats[i][1] <= expected_stats[i][1]) # check maximum bound
            # check mean by ensuring mean is within 1 std
            self.assertAlmostEqual(actual_stats[i][2], expected_stats[i][2], delta=expected_stats[i][3])
            # check skew
            self.assertAlmostEqual(actual_stats[i][4], skew(generated_resource_data[i]))
            # check kurt
            self.assertAlmostEqual(actual_stats[i][5], kurtosis(generated_resource_data[i]))
