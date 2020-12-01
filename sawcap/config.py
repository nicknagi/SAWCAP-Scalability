import logging

WORKERS = ["172.31.15.58"] # List of ip addresses of the workers in the cluster 
INTERVAL = 2 # Time in seconds to wait to detect phase change
LOG_LEVEL = logging.DEBUG # Log level for application
STACK_SIM_THRESHOLD = 0.6 # Stacktrace similarity threshold to determine phase change
DATA_DIR = "/home/ubuntu/data" # Location of folder on workers where monitor.sh dumps data
