#!/bin/bash
code_path='/home/ubuntu/capstone/archive/original/master_code'
file_path='/home/ubuntu/data'
calculate_error=1	# 0 or 1

# remove old generated phase_db files
rm $file_path/*

# run code
python3 "$code_path"/detect_anomaly.py lasso ${calculate_error}

# remove any generated files in current directory
rm ./resource_agg
rm ./threaddump_agg
