#!/bin/bash

# Redirects stderr and stdout to output.log
mkdir -p ~/logs_data_collection && \
    bash run_sawcap_on_workloads.sh $1 &> /home/ubuntu/logs_data_collection/output.log &

echo "Started the workloads script in background check ~/logs_data_collection/output.log for logs"
