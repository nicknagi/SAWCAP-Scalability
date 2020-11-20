#this file takes an aggregated thread dump file, extract all the stacks in the thread 
#dump and print the stacks in an output file
import os, sys
import signal

def get_trace(language, file_name):
	#use a list
	#set_content = []
	#use a set to avoid duplicates
	set_content = set()
	with open(file_name) as f:
		content = f.readlines()
	start = 0
	string =""
	num_threads = -1
	for line in content:
		# get number of threads
		if 'threads with trace' in line:
			num_threads = line.strip().split()[0]
		#if JAVA, we search for "Stack"
		#if C, we search for Thread
		#if line contains "stack", new stack
		if(language == 0):
			#java
			if "Stack:" in line:
				#print ("found stack start")
				start = 1
		else:
			#C
			if "(Thread" in line:
				start = 1
		if(start == 1):
			string=string+line.rstrip('\n')
			#find the last line of the trace
			if not line.rstrip('\n'):
				#print ("found stack end")
				#print(string)
				start = 0
				#for list
				#set_content.append(string)
				#for set
				set_content.add(string + " *** " + num_threads)
				num_threads = -1
				string = ""

	return set_content

def main(filename):
	stacks = get_trace(0, filename)
	total_stacks = 0
	for i in stacks:
		if 'spark' in i:
			print i
			total_stacks = total_stacks+1
	#print total_stacks

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print sys.argv[0],'<thread_dump aggregate file>'
		exit()
	main(sys.argv[1])
