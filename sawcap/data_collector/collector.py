import subprocess
import os
import csv

class WorkerData:

	def __init__(self, ipaddress):
		self.ipaddress = ipaddress.strip()
		# current id
		self.threaddump_id = -1
		self.pulled_id = 0
		self.localdatafolder = "'./temp/" + self.ipaddress + "/'"
		self.resource_id_offset = 0

class Workload:

	def __init__(self, worker_ip, timestamp, pid):
		self.worker_ip = worker_ip
		self.timestamp = timestamp
		self.pid = pid

class DataCollector:
	
	def __init__(self, workers):
	
		self.workers = []
		for worker in workers:
			workerData = WorkerData(worker)
			self.workers.append(workerData)

	# resources, threaddumps
	def getNewData(self):
		
		ret = self.get_remote_data()
		if (ret != 0):
			return 1

		all_new_data = []

		# look at all workers
		for s in self.workers:

			ip = s.ipaddress

			# get workloads
			workload_ret = self.get_workloads(ip)
			if (workload_ret != 0):
				return 2
			workloads = workload_ret[1]
			
			# server data
			new_server_data = []

			for workload in workloads:

				# get resources
				pid = workload.pid
				new_resources = []
				new_stacktraces = []

				resource_ret = self.create_resource_list(s.threaddump_id-s.pulled_id, s.ipaddress, pid, s.pulled_id)
				if (resource_ret == 0):
					new_resources = resource_ret[1]

				stacktrace_ret = self.create_threaddump_list(s.threaddump_id-s.pulled_id, s.ipaddress, pid, s.pulled_id)
				if (stacktrace_ret == 0):
					new_stacktraces = stacktrace_ret[1]
				
				new_server_data.append(pid, new_resources, new_stacktraces)

			all_new_data.append(ip, new_server_data)
		
		return all_new_data

	# returns 0 if ok, 1 if otherwise
	# does not prevent string injection attacks
	def transfer_file_if_exists(self, server, remotepath, timeout, localpath):
		command = "timeout --foreground " + timeout + " scp " + server + ":" + remotepath + " " + localpath
		return subprocess.call(command + "> /dev/null 2>&1", shell=True)

	def rsync_folder_if_exists(self, server, remotepath, timeout, localpath):
		command = "timeout --foreground " + timeout + " rsync -qrl " + server + ":" + remotepath + " " + localpath
		return subprocess.call(command + "> /dev/null 2>&1", shell=True)

	def get_ssh_file_contents(self, server, remotepath, timeout):
		command = "timeout --foreground " + timeout + " ssh -q " + server + " cat '" + remotepath + "'"
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
		for i, worker in enumerate(self.workers):
		
			os.system("mkdir -p " + worker.localdatafolder)

			retval = self.rsync_folder_if_exists(worker, "/home/ubuntu/data/", 10, worker.localdatafolder)
			if (retval != 0):
				return [retval]

			ret_threaddump_id = self.file_to_list_string(worker.localdatafolder + pid + "/current_aggregate_count")
			if (ret_threaddump_id[0] != 0):
				return ret_threaddump_id[0]

			try:
				self.workers[i].threaddump_id = int(ret_threaddump_id[1][0])
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
		ret = self.file_to_csv(self.workers[host_index].localdatafolder + "workloads")
		if (ret[0] != 0):
			return [ret[0], workloads]

		csv = ret[1]
		
		for line in csv:
			timestamp = csv[line][0]
			pid = csv[line][1]
			workload = Workload(self.workers[host_index], timestamp, pid)
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
		ret = self.file_to_csv(self.workers[host_index].localdatafolder + pid + "/resource_data")
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
				oldoffset = self.workers[host_index].resource_id_offset
				
				#if (newoffset > oldoffset):
				#	resource = [-1, -1]
				#	resource_list.append(resource)
				#	self.workers[host_index].resource_id_offset = oldoffset + 1
				#	continue

				resource = [csv[index - oldoffset][1], csv[index - oldoffset][2]]
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
			ret = self.file_to_list_string(self.workers[host_index].localdatafolder + pid + "/threaddump_aggregate_" + i)
			if (ret[0] != 0):
				stacktrace_list.append("-1")
				
			# combine all lines
			lines = ret[1]
			stacktrace_str = "\n".join(lines)
			stacktrace_list.append(stacktrace_str)
			
		return [0, stacktrace_list]
