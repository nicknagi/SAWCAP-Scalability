#!/bin/bash

if [ "$#" -ne 1 ]; then
        echo 'Usage monitor.sh <sampling interval in sec>'
        exit
fi
count=0
while true; do

	pid=`ps aux|grep 'spark.executor.CoarseGrainedExecutorBackend'|head -1`

	#echo $pid

	if [[ $pid == *"grep"* ]];then
		echo '0,0'
	else
		pid=`ps aux|grep 'spark.executor.CoarseGrainedExecutorBackend'|head -1|awk '{print $2}'`
		data=`top -p $pid -b1 -n 1|tail -1|awk '{print $9","$10}'`
		#check if the process died in the middle
		if [[ $data == *"CPU"* ]]; then
			echo '0,0'>> resource_data
		else		
			echo $data >> resource_data
		fi

		#get stacktrace info
		jstack $pid > temp_threaddump
		cat temp_threaddump | java -jar jtda-cli.jar > threaddump_aggregate_$count
		sed -i 's/<0x[0-9a-zA-Z]*>//g' threaddump_aggregate_$count
		rm -f temp_threaddump
		count=$((count+1))
	fi

	sleep $1
done
