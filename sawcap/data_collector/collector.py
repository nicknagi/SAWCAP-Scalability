import subprocess
import os
import csv
from collections import defaultdict

class WorkerData:

	def __init__(self, ipaddress):
		self.ipaddress = ipaddress.strip()
		# current id
		self.localdatafolder = "./temp/" + str(self.ipaddress) + "/"


class WorkloadID:

	def __init__(self, worker_ip, timestamp, pid):
		self.worker_ip = worker_ip
		self.timestamp = timestamp
		self.pid = pid
		self.data_id = -1
		self.pulled_id = 0
		self.resource_id_offset = 0


class DataCollector:

	def __init__(self, workers):

		self.workers = []
		for worker in workers:
			workerData = WorkerData(worker)
			self.workers.append(workerData)

	# returns
	# (server list)
	# 			-> (ip, pid list)
	#						-> (pid, count id, resources list, stacktraces list)
	def get_new_data(self, window_size):

		ret = self.get_remote_data()
		if (ret != 0):
			return 1

		all_new_data = []

		# look at all workers
		for s in self.workers:

			ip = s.ipaddress

			# get workloads
			workload_ret = self.get_workloads(ip)
			if (workload_ret[0] != 0):
				return 2
			workloads = workload_ret[1]

			# server data
			new_server_data = []
			for workload in workloads:

				# get resources
				pid = workload.pid
				new_resources = []
				new_stacktraces = []

				# update data_id
				count_ret = self.update_data_id(workload)
				if (count_ret != 0):
					return 3
				# pulled id updates here
				while (workload.data_id - workload.pulled_id >= window_size):
					resource_ret = self.create_resource_list(
						window_size, workload.worker_ip, pid, workload.pulled_id)
					if (resource_ret[0] == 0):
						new_resources = resource_ret[1]

					stacktrace_ret = self.create_threaddump_list(
						window_size, workload.worker_ip, pid, workload.pulled_id)
					if (stacktrace_ret[0] == 0):
						new_stacktraces = stacktrace_ret[1]

					# new_server_data.append([pid, s.pulled_id, new_resources, new_stacktraces])
					new_data_dict = {}
					new_data_dict["pid"] = pid
					new_data_dict["count_id"] = workload.pulled_id
					new_data_dict["raw_resource_data"] = new_resources
					new_data_dict["stacktrace_data"] = new_stacktraces
					workload.pulled_id = workload.pulled_id + window_size
					new_server_data.append(new_data_dict)

			all_data_dict = {}
			all_data_dict["ip"] = ip
			all_data_dict["data"] = new_server_data
			all_new_data.append(all_data_dict)

		return all_new_data

	# returns 0 if ok, 1 if otherwise
	# does not prevent string injection attacks
	def transfer_file_if_exists(self, server, remotepath, timeout, localpath):
		command = "timeout --foreground " + \
			str(timeout) + " scp " + server + ":" + remotepath + " " + localpath
		return subprocess.call(command + "> /dev/null 2>&1", shell=True)

	def rsync_folder_if_exists(self, server, remotepath, timeout, localpath):
		command = "timeout --foreground " + \
			str(timeout) + " rsync -qrl " + server + ":" + remotepath + " " + localpath
		return subprocess.call(command + "> /dev/null 2>&1", shell=True)

	def get_ssh_file_contents(self, server, remotepath, timeout):
		command = "timeout --foreground " + \
			str(timeout) + " ssh -q " + server + " cat '" + remotepath + "'"
		try:
			output = subprocess.check_output(command, shell=True)
			return [0, output]
		except subprocess.CalledProcessError as err:
			return [err.returncode, err.output]

	# Returns -1 if err, index if succeeds
	def index_of_host(self, ipaddress):

		for i, worker in enumerate(self.workers):
			if (worker.ipaddress == ipaddress):
				return i

		return -1

	# Returns err, list(string)

	def file_to_list_string(self, localpath):

		lines = []

		try:
			with open(localpath) as f:
				lines = f.readlines()
		except EnvironmentError:
			return [1, lines]

		lines = [i.strip() for i in lines]
		return [0, lines]

	# Returns err, list(list(string))
	def file_to_csv(self, localpath):

		try:
			with open(localpath, newline='') as f:
				reader = csv.reader(f)
				data = list(reader)
				return [0, data]

		except EnvironmentError:
			return [1, []]

		return [1, []]

	# Copy all data to local machine
	# Returns err
	def get_remote_data(self):

		# fetch new data
		for worker in self.workers:

			os.system("mkdir -p " + worker.localdatafolder)

			retval = self.rsync_folder_if_exists(
				worker.ipaddress, "/home/ubuntu/data/", 10, worker.localdatafolder)
			if (retval != 0):
				return [retval]

		return 0

	# Update current data_id from file
	# Returns err
	def update_data_id(self, workload_id):

		# get host data
		host_index = self.index_of_host(workload_id.worker_ip)
		if (host_index < 0):
			return 1
		ret_data_id = self.file_to_list_string(
			self.workers[host_index].localdatafolder + workload_id.pid + "/current_aggregate_count")
		if (ret_data_id[0] != 0):
			return ret_data_id[0]

		try:
			workload_id.data_id = int(ret_data_id[1][0])
		except IndexError:
			return 1

		return 0

	# Return err, workloads
	def get_workloads(self, ipaddress):

		workloads = []

		# get host data
		host_index = self.index_of_host(ipaddress)
		if (host_index < 0):
			return [1, workloads]

		# get csv
		ret = self.file_to_csv(
			self.workers[host_index].localdatafolder + "workloads")
		if (ret[0] != 0):
			return [ret[0], workloads]

		csv = ret[1]

		for line in csv:
			timestamp = line[0]
			pid = line[1]
			workload = WorkloadID(self.workers[host_index].ipaddress, timestamp, pid)
			workloads.append(workload)
		return [0, workloads]

	# Returns err, resource-list: [cpu, mem]
	# This expects the resource file is in order with no miss numbers!!!!
	def create_resource_list(self, window_size, ipaddress, pid, _start_id):

		resource_list = []

		# get host data
		host_index = self.index_of_host(ipaddress)
		if (host_index < 0):
			return [1, resource_list]

		# get csv
		ret = self.file_to_csv(
			self.workers[host_index].localdatafolder + pid + "/resource_data")
		if (ret[0] != 0):
			return [ret[0], resource_list]

		csv = ret[1]

		# check errors
		start_id = 0
		end_id = 0
		try:
			start_id = int(_start_id)
			end_id = int(start_id) + window_size
		except Exception:
			return [1, resource_list]

		if (end_id < start_id):
			return [1, resource_list]

		# get resources
		try:
			for index in range(start_id, end_id):

				# if resource id has missing data, does not tolerate multiple missing data points well
				#resource_id = csv[i][0]
				#newoffset = resource_id - index
				# CHANGE THIS
				#oldoffset = self.workers[host_index].resource_id_offset
				oldoffset = 0

				#if (newoffset > oldoffset):
				#	resource = [-1, -1]
				#	resource_list.append(resource)
				#	self.workers[host_index].resource_id_offset = oldoffset + 1
				#	continue
				cpu = csv[index - oldoffset][1]
				mem = csv[index - oldoffset][2]

				if(cpu in (None, "")):
					cpu = -1

				if (mem in (None, "")):
					mem = -1

				resource = [cpu, mem]
				resource_list.append(resource)

		except Exception:
			return [1, resource_list]

		return [0, resource_list]

	# if stacktrace unavailable, the string will be -1
	def create_threaddump_list(self, window_size, ipaddress, pid, _start_id):

		stacktrace_list = []

		# get host data
		host_index = self.index_of_host(ipaddress)
		if (host_index < 0):
			return [1, stacktrace_list]

		# check errors
		start_id = 0
		end_id = 0
		try:
			start_id = int(_start_id)
			end_id = start_id + window_size
		except Exception:
			return [1, stacktrace_list]

		if (end_id < start_id):
			return [1, stacktrace_list]

		# get stacktraces
		for i in range(start_id, end_id):
			ret = self.file_to_list_string(
				self.workers[host_index].localdatafolder + str(pid) + "/threaddump_aggregate_" + str(i))
			if (ret[0] != 0):
				stacktrace_list.append("-1")

			# combine all lines
			lines = ret[1]
			stacktrace_str = "\n".join(lines)
			stacktrace_list.append(stacktrace_str)

		return [0, stacktrace_list]
