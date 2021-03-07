#!/bin/bash

data_dir="/home/ubuntu/data"
if [ "$#" -ne 1 ]; then
        echo 'Usage monitor.sh interval (in s)'
        exit
fi

# Start API server to get worker data
private_ip_address=$(ip addr show | grep -o "inet 192.[0-9]*\.[0-9]*\.[0-9]*" | grep -o "192.[0-9]*\.[0-9]*\.[0-9]*")
gunicorn worker_data_api:app -b "$private_ip_address":8690 --reload --log-level DEBUG &> worker_data_api.log

while true; do

	pid=`jps | grep CoarseGrainedExecutorBackend | awk '{print $1}'`
	timestamp=$(date +%s)

	if [[ -z "${pid}" ]]
	then
    	echo "no workload running"
		echo '0,0' > "${data_dir}/resource_data"
		> "${data_dir}/threaddump_data"

	else
		echo "Currently Observing ${pid}"

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

	fi
	sleep $1

done
