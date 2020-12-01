import subprocess
import os

class DataCollector:

	servers = []
	
	def __init__(self, servers):
		self.servers = servers

	# returns 0 if ok, 1 if otherwise
	# does not prevent string injection attacks
	def transfer_file_if_exists(self, server, remotepath, timeout, localpath):
		command = "timeout --foreground " + timeout + " scp " + server + ":" + remotepath + " " + localpath
		return subprocess.call(command + "> /dev/null 2>&1", shell=True)

	def get_ssh_file_contents(self, server, remotepath, timeout):
		command = "timeout --foreground " + timeout + " ssh -q " + server + " cat '" + remotepath + "'"
		try:
			output = subprocess.check_output(command, shell=True)
			return [0, output]
		except subprocess.CalledProcessError as err:
			return [err.returncode, err.output]

	def parse_resource_agg(self, file):

		# takes an input file which has one line per server for CPU and Mem
		# returns an aggregate of three
		lines = []
		with open(file) as f:
			lines = f.readlines()

		# process line by line
		resource_usage = [0] * len(lines[0].split(','))
		# print("Number of resources ", resource_usage)
		for line in lines:
			usages = line.split(',')
			for i in range(len(usages)):
				resource_usage[i] += float(usages[i])

		resource_usage = [float(i) / len(self.servers) for i in resource_usage]

		return resource_usage

	def stacktrace_helper(self):
		# this function connects to the servers, fetches the threaddump, aggregates
		# them and extract threaddump and resource usage information from them
		# returns a list containing the threaddump and resource info

		# clear the prev buffer
		os.system("> ./threaddump_agg")
		os.system("> ./resource_agg")

		# fetch new data
		for s in self.servers:
			# accumulate threaddumps
			# When anomaly is run in any of the slaves, ssh also takes longer, so the timeout heuristics
			# is simple but powerful to detect those anomalies, though the timeout value should change
			# system to system
			retcount = self.get_ssh_file_contents(s, "/home/ubuntu/data/current_aggregate_count", 10)
			if (retcount[0] != 0):
				return [1, set([]), []]

			count = int(retcount[1])

			retval = self.transfer_file_if_exists(s, "/home/ubuntu/data/threaddump_aggregate_" + count, 10, "./threaddump_agg")
			# accumulate resource usage
			self.transfer_file_if_exists(s, "/home/ubuntu/data/resource_data", 10, "./resource_agg")

		functions = []
		with open("./threaddump_agg") as f:
			functions = f.readlines()

		resource_agg = self.parse_resource_agg("./resource_agg")
		functions = [i.strip() for i in functions]

		return [retval, set(functions), resource_agg]
