#!/bin/bash

# Redirects stderr and stdout to output.log
mkdir -p ~/logs_data_collection && \
    bash run_sawcap_on_workloads.sh &> /home/ubuntu/logs_data_collection/output.log &
