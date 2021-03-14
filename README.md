# Capstone Project - Semantic-Aware Resource Characterization and Prediction

> This is the Official Github repo for the capstone project

Team Members:

1. Gerin
2. Nekhil
3. Joshua
4. Polina

## Coding Guidelines

* Most of the codebase is in Python. Let us try to use Python for most of our work unless required otherwise. This reduces mental overhead when context switching between different languages.

* Follow the Python PEP8 coding style guidelines. This ensures consisteny in the codebase. Major points to keep in mind:

        Snake case for variables: this_is_a_variable = 5

        Class names use camel case: ClassName

        Be descriptive with names: instead of x = 5 -- use number_of_machines = 5 etc.
        
* Try to use pure functions whenever possible, i.e when you have a function with some arguments do not modify the data passed in through the arguments directly instead return the output. In other words, if you'd like functions to be pure, then do not change the value of the input or any data that exists outside the function's scope. (FYI functions in python have arguments passed by reference)

## Running Arnamoy's original code

### Prerequisites
 * 3 VMs setup with SSH access to them
     * `Runner`: runs actual code and HiBench workloads
     * `Master`: Spark Master Node, starts Hadoop
     * `Slave`: Spark worker node, can potentially have many slaves

### Steps
1. SSH into `Master` and start Hadoop
```
bash /home/ubuntu/capstone/scripts/start_hadoop.sh
```

2. SSH into `Slave` and start the monitor script
```
python3 /home/ubuntu/capstone/archive/original/slave_code/monitor.py
```

> :warning: **Ensure the script is writing to the correct directory**: The file that it writes to should be the same file that the anomaly detection code reads from.

3. SSH into `Runner` to start anomaly detection script. A script to run the original code and calculate accuracy has been provided for ease of use. Edit script to set `calculate_error=0` if you don't want to record accuracy calculations.
```
bash /home/ubuntu/capstone/scripts/run_original_code.sh
```

> :warning: **Be careful of memory overhead**: Calculating accuracy involves saving every single actual and predicted value and calculating the error at the end. To eliminate unecessary memory overhead, turn off accuracy calculations when testing scalability

4. SSH into `Runner` to run HiBench workloads.
* first prepare a workload
```
bash /home/ubuntu/HiBench/bin/workloads/<workload>/prepare/prepare.sh
```
* then run a workload
```
bash /home/ubuntu/HiBench/bin/workloads/<workload>/spark/run.sh
```
* you can also view the summarized workload report at `<HiBench_Root>/report/hibench.report`

5. Generate an anomaly in `Slave` using `stress`
```
sudo stress --cpu 64
```

6. Turn off the cluster when you're done by using the script in `Master`
```
bash /home/ubuntu/capstone/scripts/stop_hadoop.sh
```

### Output
* If everything worked, you should see the output on `Runner` consisting of zeros when nothing is running
> Actual: ['0.00', '0.00'] Predicted: ['0.00', '0.00']  
> Actual: ['0.00', '0.00'] Predicted: ['0.00', '0.00']

* When a workload is running you should see actual and predicted values
> Actual: ['93.30', '14.90'] Predicted: ['0.00', '0.00']  
> Actual: ['100.00', '10.40'] Predicted: ['83.18', '14.90']

* The first value is the CPU usage and the second value is the Memory usage
* To exit the program, you can type `Ctrl + C` and view the prediction accuracy if it was enabled
> ### Error Rates ###  
> Error CPU: 29.181 %  
> Error MEM: 16.451 %  

## Data collection
The data collection script does the following
- Prepares HiBench workloads
- Runs HiBench workloads a specified number of times
- Runs `sawcap.py` for each workload

Use the following command to start the data collection process
```
 bash $HOME/capstone/sawcap/run_sawcap_on_workloads.sh arg1
```
arg1 - if set runs the original code and the refatored code. Otherwise only the refactored code.

The results are exported to `$HOME/data/sawcap_stats.txt`

Use the following command to start the data collection process in the background (as it can take hours)
```
 bash $HOME/capstone/sawcap/run_workloads_in_background.sh arg1
```
arg1 - if set runs the original code and the refatored code. Otherwise only the refactored code.

The results are exported to `$HOME/data/sawcap_stats.txt`

You must also run the monitor script on each slave as follows (or see section on Enable or Disable Monitoring)
```
bash $HOME/capstone/sawcap/runner/monitor.sh 1
```

## Infrastructure
There are 2 scripts in the infrastructure folder. 

Both scripts should be run from the orchestrator droplet in Digital Ocean as it has access to all the droplets that the script spins up as well as the API token.

### SpinUp A Cluster
```
python3 spinupcluster.py --numworkers X [--uniqueid NAME]
```
--numworkers is the number of workers in the hadoop cluster

--uniqueid is the identifier/name of the cluster you want

--workload_scale (optional) - default is large. is the setting for hibench.scale.profile  in hibench.conf

--start_data_collection (optional) - start the data collection script after cluster spinup

> Note: uniqueid is an optional parameter, if you do not specify it it uses the current time as the id

### Teardown A Cluster
```
python3 teardowncluster.py --uniqueid NAME
```
--uniqueid is the identifier/name of the cluster you want to teardown

### Enable or Disable Monitoring
```
python3 monitoring.py --uniqueid NAME [--stop] [--interval X]
```
--uniqueid is the identifier/name of the cluster you want to enable or disable monitoring on.

--stop option to indicate that monitoring should be disabled. If not provided, then monitoring is enabled.

--interval argument provided to monitor.sh i.e sampling interval

digitalocean python wrapper used in scripts: https://github.com/koalalorenzo/python-digitalocean

### Visually compare statistics across different workloads and different algorithms
```
python3 graph_comparison.py [-h] --dir_name DIR_NAME --stats STATS --stat_files
                           STAT_FILES --algos ALGOS [--save_path SAVE_PATH]
```
--dir_name is the directory name with all files

--stats is a list of stats to compare, separated by a comma without space

--stat_files is a list of data files to compare, separated by a comma without space

--algos is a list of algo names associated with stat files, , separated by a comma without space

--save_path is a save path for graphs

###### Example usage:
```
python graph_comparison.py --dir_name ~/Desktop/capstone/sawcap --stats CPU,MEM --stat_files sawcap_stats.txt 
                           --algos lasso --save_path ~/Desktop/capstone/sawcap/
```

### Generate reports comprising of max, min and average of metrics
The metrics includes cpu, memory, latency, upload, download speed as well as the frequency of predictions.

Generate report of all metrics:
```
python3 metrics_query.py -uid <unique-id-of-experiment> --all
```
