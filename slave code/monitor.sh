#!/bin/bash

if [ "$#" -ne 1 ]; then
        echo 'Usage monitor.sh pid'
        exit
fi

	if [[ $1 == '0' ]];then
		echo '0,0' > resource_data
		> threaddump_data
	else
		data=`top -p $1 -b1 -n 1|tail -1|awk '{print $9","$10}'`
		#check if the process died in the middle
		if [[ $data == *"CPU"* ]]; then
			echo '0,0' > resource_data
		else		
			echo $data > resource_data
		fi

		#get stacktrace info
		jstack $1 > temp_threaddump
		cat temp_threaddump | java -jar jtda-cli.jar > threaddump_aggregate
		sed -i 's/<0x[0-9a-zA-Z]*>//g' threaddump_aggregate
		python get_stacks.py threaddump_aggregate > threaddump_data
	fi
