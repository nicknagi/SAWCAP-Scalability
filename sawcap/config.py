import logging

WORKERS = ['192.168.0.10', '192.168.0.11', '192.168.0.12']
INTERVAL = 2 # Time in seconds to wait to detect phase change
LOG_LEVEL = logging.CRITICAL # Log level for application
STACK_SIM_THRESHOLD = 0.6 # Stacktrace similarity threshold to determine phase change
DATA_DIR = "/home/ubuntu/data" # Location of folder on workers where monitor.sh dumps data
STATS_FILE = "/sawcap_stats.txt"    # file to save reported accuracy values to
BATCH_SIZE = 3 # Number of profiles needed for a phase to train a model
NUM_RESOURCES = 2 # Number of resources; Currently - cpu, mem
ENABLE_STATS = True # Enable collection and printing of stats
ALGO = "lasso" # Defines prediction model
ANOMALY_DETECTION_ENABLED = True
