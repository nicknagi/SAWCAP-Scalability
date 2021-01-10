import logging

WORKERS = [""] # List of ip addresses of the workers in the cluster 
INTERVAL = 2 # Time in seconds to wait to detect phase change
LOG_LEVEL = logging.DEBUG # Log level for application
STACK_SIM_THRESHOLD = 0.6 # Stacktrace similarity threshold to determine phase change
DATA_DIR = "/home/ubuntu/data" # Location of folder on workers where monitor.sh dumps data
BATCH_SIZE = 3 # Number of profiles needed for a phase to train a model
NUM_RESOURCES = 2 # Number of resources; Currently - cpu, mem
ENABLE_STATS = True # Enable collection and printing of stats