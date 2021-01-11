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
python3 /home/ubuntu/capstone/archive/original/slave code/monitor.py
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
 bash $HOME/capstone/sawcap/run_sawcap_on_workloads.sh
```
The results are exported to `$HOME/data/sawcap_stats.txt`

## Infrastructure
There are 2 scripts in the infrastructure folder. 

Both scripts should be run from the orchestrator droplet in Digital Ocean as it has access to all the droplets that the script spins up as well as the API token.

### SpinUp A Cluster
```
python3 spinupcluster.py --numworkers X --uniqueid NAME
```
--numworkers is the number of workers in the hadoop cluster

--uniqueid is the identifier/name of the cluster you want

> Note: uniqueid is an optional parameter, if you do not specify it it uses the current time as the id

### Teardown A Cluster
```
python3 teardowncluster.py --uniqueid NAME
```
--uniqueid is the identifier/name of the cluster you want to teardown

digitalocean python wrapper used in scripts: https://github.com/koalalorenzo/python-digitalocean
