#!/bin/bash

main_data_dir="/home/ubuntu/data"
rm -rf "${main_data_dir}/*"

if [ "$#" -ne 1 ]; then
        echo 'Usage monitor.sh <sampling interval in sec>'
        exit
fi
count=0
while true; do

	pid=`jps | grep CoarseGrainedExecutorBackend | awk '{print $1}'`
	# while IFS= read -r SINGLELINE; do
		# echo $SINGLELINE;
	# done
	timestamp=$(date +%s)
	
	if [[ -z "${pid}" ]]
    then
    	count=0
    	echo "no workload running"
    	sleep 5
		continue

	else
		data_dir="${main_data_dir}/${pid}"
		mkdir -p "${data_dir}"
		echo "${timestamp},${pid}" >> "${main_data_dir}/workloads"

		pid=`jps | grep CoarseGrainedExecutorBackend | awk '{print $1}'`
		data=`top -p $pid -b1 -n 1|tail -1|awk '{print $9","$10}'`
		#check if the process died in the middle
		if [[ $data == *"CPU"* ]]; then
			echo '0,0,0' >> "${data_dir}/resource_data"
		else
			echo "$count,$data" >> "${data_dir}/resource_data"
		fi

		#get stacktrace info
		jstack $pid > "${data_dir}/temp_threaddump"
		cat "${data_dir}/temp_threaddump" | java -jar jtda-cli.jar > "${data_dir}/threaddump_aggregate_${count}"
		sed -i 's/<0x[0-9a-zA-Z]*>//g' "${data_dir}/threaddump_aggregate_${count}"
		rm -f "${data_dir}/temp_threaddump"

		echo "${count}" > "${data_dir}/current_aggregate_count"
		count=$((count+1))
	fi

	sleep $1
done
