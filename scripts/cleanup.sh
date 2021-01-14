#!/bin/bash

pkill -ef "sawcap.py"
pkill -ef "detect_anomaly.py "
pkill -ef "bash /usr/local/HiBench/bin/workloads*"
pkill -ef "bash run_workloads_in_background.sh*"
pkill -ef "bash run_sawcap_on_workloads.sh*"

sleep 2
ps aux | grep bash
ps aux | grep python3
echo "Done"