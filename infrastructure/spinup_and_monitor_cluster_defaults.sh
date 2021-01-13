#!/bin/bash

if [ $# -eq 0 ]
  then
    echo "No arguments supplied, specify the uniqueid of the cluster"
fi

python3 spinupcluster.py --numworkers 3 --uniqueid $1 && python3 monitoring.py --uniqueid $1
