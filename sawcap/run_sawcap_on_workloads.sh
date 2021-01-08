#!/bin/bash

# colours for printing
ORANGE='\033[0;33m'
RED='\033[0;31m'
LRED='\033[1;31m'
LPURPLE='\033[1;35m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# file paths
workload_dir="$HIBENCH_WORKLOAD_DIR"
prepare_path="/micro/wordcount/prepare/prepare.sh"
run_path="/micro/wordcount/spark/run.sh"
data_dir="/home/ubuntu/data"
stats_path="${data_dir}/sawcap_stats.txt"
code_path='/home/ubuntu/capstone/archive/original/master code'

# number of times we run a workload
NUM_ITER=2

# Printing
# I: info
# E: error

print_starting_prepare () {
    echo -e "${ORANGE}\n[I] ${YELLOW}Preparing $1 ${NC} \n"
}

print_starting_run () {
    echo -e "${ORANGE}\n[I] ${YELLOW}Running $1 $2 ${NC} \n"
}

# param1: error message
print_error () {
    echo -e "${RED}\n[E] $1 ${NC} \n"
}

# param1: PID of python process
print_stop_sawcap () {
    echo -e "${ORANGE}\n[I] Sending SIGINT to process $1 ${NC} \n"
}

# prepare workload once
# param1: path
# param2: workload name
prepare_workload () {
    print_starting_prepare $2
	bash $1
	return $?   # return code
}

# run workload once
# param1: path
# param2: workload name
run_workload () {
    print_starting_run $2
    bash $1
    return $?
}

run_sawcap () {
    python3 "$code_path"/detect_anomaly.py lasso 1 &
    return $?
}

# param1: PID of python process
stop_sawcap () {
    KILL_PID=$1
    print_stop_sawcap $KILL_PID
    kill -15 $KILL_PID      # SIGTERM
    sleep 10     # wait for process to die
}

# START SCRIPT

# delete previously collected data
rm -f $stats_path

# prepare
prepare_workload "$workload_dir$prepare_path" "wordcount"
ret_code=$?

if [ $ret_code -eq 0 ]
then
    # prepare was successful    
    for (( i=1; i<=$NUM_ITER; i++ ))
    do
        run_sawcap
        PID=$!

        run_workload "$workload_dir$run_path" "wordcount $i"
        ret_code=$?

        # kill sawcap to export stats
        stop_sawcap $PID

        if [ $ret_code -gt 0 ]
        then
            print_error "HiBench workload failed"
            exit   
        fi
    done
    
    exit
else
    print_error "HiBench prepare failed"
    exit
fi
