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
data_dir="$HOME/data"
stats_path="${data_dir}/sawcap_stats.txt"
code_path="$HOME/capstone/sawcap/sawcap.py"
db_path="${data_dir}/2020266_phase_db_*"

original_db_path="${data_dir}/phase_db_*"
original_stats_path="${data_dir}/original_code_stats.txt"
original_code_path="$HOME/capstone/archive/original/master code/detect_anomaly.py lasso"

# workloads
bayes_prepare="/ml/bayes/prepare/prepare.sh"
bayes_run="/ml/bayes/spark/run.sh"
bayes_name="bayes"

nweight_prepare="/graph/nweight/prepare/prepare.sh"
nweight_run="/graph/nweight/spark/run.sh"
nweight_name="nweight"

kmeans_prepare="/ml/kmeans/prepare/prepare.sh"
kmeans_run="/ml/kmeans/spark/run.sh"
kmeans_name="kmeans"

pagerank_prepare="/graph/pagerank/prepare/prepare.sh"
pagerank_run="/graph/pagerank/spark/run.sh"
pagerank_name="pagerank"

svm_prepare="/ml/svm/prepare/prepare.sh"
svm_run="/ml/svm/spark/run.sh"
svm_name="svm"

wordcount_prepare="/micro/wordcount/prepare/prepare.sh"
wordcount_run="/micro/wordcount/spark/run.sh"
wordcount_name="wordcount"

rf_prepare="/ml/rf/prepare/prepare.sh"
rf_run="/ml/rf/spark/run.sh"
rf_name="rf"

# number of times we run a workload
NUM_ITER=3

# Check wether to run original code
should_run_original_code=$1

# Printing
# I: info
# E: error

print_starting_prepare () {
    echo -e "${ORANGE}\n[I] ${YELLOW}Preparing $1 ${NC} \n"
}

print_starting_run () {
    echo -e "${ORANGE}\n[I] ${YELLOW}Running $1 $2 $3 $4 ${NC} \n"
}

# param1: error message
print_error () {
    echo -e "${RED}\n[E] $1 ${NC} \n"
}

# param1: error message
print_warning () {
    echo -e "${ORANGE}\n[I] $1 ${NC} \n"
}

# param1: PID of python process
print_stop_sawcap () {
    echo -e "${ORANGE}\n[I] Sending SIGTERM to process $1 ${NC} \n"
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
    python3 "$code_path" &
    return $?
}

run_original_code () {
    python3 "$original_code_path" &
    return $?
}

# param1: PID of python process
stop_sawcap () {
    KILL_PID=$1
    print_stop_sawcap $KILL_PID
    kill -15 $KILL_PID      # SIGTERM
    sleep 10     # wait for process to die
}

# param1: name of workload
# param2: path to prepare workload
# param3: path to run workload
start_data_collection () {
    workload_name=$1
    prepare_path=$2
    run_path=$3

    # clear hdfs to save space
    hdfs dfs -rm -R -skipTrash "/*"
    sleep 5

    # prepare
    prepare_workload "$workload_dir$prepare_path" "$workload_name"
    ret_code=$?
    num_fails=0

    if [ $ret_code -eq 0 ]
    then
        # prepare was successful 
        i=0
        while [ $i -lt $NUM_ITER ]
        do
            run_sawcap
            PID=$!

            if [ ! -z "${should_run_original_code}" ]
            then
                run_original_code
                O_PID=$!
                echo -e "\n$workload_name" >> $original_stats_path
            fi

            echo -e "\n$workload_name" >> $stats_path

            run_workload "$workload_dir$run_path" "$workload_name $i fails: $num_fails"
            ret_code=$?

            # kill sawcap to export stats if pid exists, else retry workload (for example if anomaly detected sawcap pid will not exist)
            if ps -p $PID > /dev/null
            then
                 stop_sawcap $PID
            else
                 print_warning "sawcap.py process does not exist, retrying workload"
                 echo "sawcap failure; disregard stat $workload_name $i" >> $stats_path
                 sleep 5
                 continue
            fi

            # Stop the original code if running
            if [ ! -z "${should_run_original_code}" ]
            then
                stop_sawcap $O_PID
            fi

            if [ $ret_code -gt 0 ]
            then
                print_warning "HiBench workload failed incrementing num_fails"
                echo "workload failure; disregard stat $workload_name $i" >> $stats_path
                num_fails=$((num_fails+1))
                sleep 30
                if [ $num_fails -eq 3 ]
                then
                    print_error "HiBench workload failed 3 times, exiting"
                    exit
                fi
            else
                num_fails=0
                i=$((i+1))
                sleep 5
            fi
        done

    else
        print_error "HiBench prepare failed"
        exit
    fi

}

# START SCRIPT

# delete previously collected data
rm -f $stats_path

# delete sawcap database
rm -f $db_path

if [ ! -z "${should_run_original_code}" ]
then
    rm -f $original_db_path
fi

# run bayes
# start_data_collection $bayes_name $bayes_prepare $bayes_run 

# run nweight
start_data_collection $nweight_name $nweight_prepare $nweight_run

# run kmeans
start_data_collection $kmeans_name $kmeans_prepare $kmeans_run 

# run pagerank
start_data_collection $pagerank_name $pagerank_prepare $pagerank_run 

# run svm
start_data_collection $svm_name $svm_prepare $svm_run 

# run wordcount
start_data_collection $wordcount_name $wordcount_prepare $wordcount_run 

# run rf
start_data_collection $rf_name $rf_prepare $rf_run 
