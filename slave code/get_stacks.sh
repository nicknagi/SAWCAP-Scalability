#!/bin/bash

data_dir="/home/ubuntu/data"

if [ "$#" -ne 1 ]; then
        echo 'Usage monitor.sh <sampling interval in sec>'
        exit
fi
count=0
while true; do

	pid=`jps | grep CoarseGrainedExecutorBackend | awk '{print $1}'`

	#echo $pid

	if [[ -z "$pid"]] then
		echo '0,0'
	else
		pid=`jps | grep CoarseGrainedExecutorBackend | awk '{print $1}'`
		data=`top -p $pid -b1 -n 1|tail -1|awk '{print $9","$10}'`
		#check if the process died in the middle
		if [[ $data == *"CPU"* ]]; then
			echo '0,0'>> "${data_dir}/resource_data"
		else		
			echo $data >> "${data_dir}/resource_data"
		fi

		#get stacktrace info
		jstack $pid > "${data_dir}/temp_threaddump"
		cat "${data_dir}/temp_threaddump" | java -jar jtda-cli.jar > "${data_dir}/threaddump_aggregate_${count}"
		sed -i 's/<0x[0-9a-zA-Z]*>//g' "${data_dir}/threaddump_aggregate_${count}"
		rm -f "${data_dir}/temp_threaddump"
		count=$((count+1))
	fi

	sleep $1
done
