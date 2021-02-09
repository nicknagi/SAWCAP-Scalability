#!/bin/bash

pip3 install psutil influxdb numpy && \
apt install -y nethogs && \
(nethogs -t -d 1 | python3 /home/ubuntu/capstone/sawcap/sawcap_resource_monitor.py) > /dev/null 2>&1 &

echo "---------------------------------- Done starting sawcap resource monitoring ---------------------------------"