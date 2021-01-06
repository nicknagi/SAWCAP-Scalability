#!/bin/bash

data_dir="/home/ubuntu/data"
mkdir -p ${data_dir}
if [ "$#" -ne 1 ]; then
        echo 'Usage monitor.sh pid'
        exit
fi

	if [[ $1 == '0' ]];then
		echo '0,0' > "${data_dir}/resource_data"
		> "${data_dir}/threaddump_data"
	else
		data=`top -p $1 -b1 -n 1|tail -1|awk '{print $9","$10}'`
		#check if the process died in the middle
		if [[ $data == *"CPU"* ]]; then
			echo '0,0' > "${data_dir}/resource_data"
		else		
			echo $data > "${data_dir}/resource_data"
		fi

		#get stacktrace info
		jstack $1 > "${data_dir}/temp_threaddump"
		cat "${data_dir}/temp_threaddump" | java -jar jtda-cli.jar > "${data_dir}/threaddump_aggregate"
		sed -i 's/<0x[0-9a-zA-Z]*>//g' "${data_dir}/threaddump_aggregate"
		python get_stacks.py "${data_dir}/threaddump_aggregate" > "${data_dir}/threaddump_data"
	fi
