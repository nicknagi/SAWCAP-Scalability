#!/bin/bash

pip3 install psutils influxdb && \
apt install -y nethogs && \
nethogs -t -d 1 | python3 /home/ubuntu/capstone/sawcap/metrics/sawcap_resource_monitor.py