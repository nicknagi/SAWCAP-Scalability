# CAPSTONE

Code changes to make it run:

- Keep all the files of slave_code in the same directory
- Do the following for all the slaves:
- Setup passwordless ssh from master to all the slaves
- Make the following changes in the detect_anomaly.py (to be run from a node that can passwordless communicate with the slaves)
- Provide IP address of the slaves in line 11
- Change the path for the phase database, the phase database is created where the monitor script is run from (line 52, 162, 484, 528, 529)
- Change the path 219 and 223 to reflect the path in each of the slave where you stores the slave_code content.  The profile data is collected at each slave node in the same directory where you run the monitor.py from.  You have to give this path to the detect_anomaly


Deploy steps:

1. Setup a Spark Cluster (master-slave, you can start with a 4-node cluster), with hadoop (https://medium.com/@jeevananandanne/setup-4-node-hadoop-cluster-on-aws-ec2-instances-1c1eeb4453bd), install Hibench
2. Start the cluster
3. Start monitoring in each slave node -->  python monitor.py &
4. Start the anomaly detection script in a node (either master or a separate node that can communicate with the slaves, this node should not necessarily be the part of spark cluster).  The agg argument specifies a simple yet effective aggregate algorithm for anomaly detection --> python detect_anomaly.py agg
5. When no workload is running, you should see output like:
('Actual:', ['0.00', '0.00'], 'Predicted:', ['0.00', '0.00'])
('Actual:', ['0.00', '0.00'], 'Predicted:', ['0.00', '0.00'])
6. Start running a workload.  The output of detect_anomaly should change to non-zero values for predicted and actual
7. Generate an anomaly in any of the slaves using stress --> sudo stress --cpu 64
8. The detect_anomaly script should report the anomaly and exit, showing the current stacktrace of the phase.


