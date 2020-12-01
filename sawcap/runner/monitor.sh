#!/bin/bash

data_dir="/home/ubuntu/data"
mkdir -p ${data_dir}
if [ "$#" -ne 1 ]; then
        echo 'Usage monitor.sh interval (in s)'
        exit
fi

count=0
prev_pid=""
while true; do

	pid=`jps | grep CoarseGrainedExecutorBackend | awk '{print $1}'`
	timestamp=$(date +%s)

	if [[ -z "${pid}" ]]
    	then
    	count=0
    	echo "no workload running"
    	sleep 5
		continue

	else
		echo "Currently Observing ${pid}"
		# # Track prev_pid for the very first job
		# if [[ "${prev_pid}" == "" ]]
		# then
		# 	echo "${timestamp},${pid}" >> "${data_dir}/workloads"
		# 	prev_pid=${pid}
		# fi

		# # Write data to workloads file for new pid
		# if [[ "${prev_pid}" != "${pid}" ]]
		# then
		# 	echo "${timestamp},${pid}" >> "${data_dir}/workloads"
		# 	prev_pid=${pid}
		# fi
		# echo "${pid}" >> "${data_dir}/pid"
	fi


	data=`top -p ${pid} -b1 -n 1|tail -1|awk '{print $9","$10}'`
	#check if the process died in the middle
	if [[ $data == *"CPU"* ]]; then
		echo '0,0' > "${data_dir}/resource_data"
	else		
		echo $data > "${data_dir}/resource_data"
	fi

	#get stacktrace info
	jstack ${pid} > "${data_dir}/temp_threaddump"
	cat "${data_dir}/temp_threaddump" | java -jar jtda-cli.jar > "${data_dir}/threaddump_aggregate"
	sed -i 's/<0x[0-9a-zA-Z]*>//g' "${data_dir}/threaddump_aggregate"
	python get_stacks.py "${data_dir}/threaddump_aggregate" > "${data_dir}/threaddump_data"

	sleep $1

done
