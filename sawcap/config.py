import logging

WORKERS = ['192.168.0.5', '192.168.0.6', '192.168.0.7']
INTERVAL = 2 # Time in seconds to wait to detect phase change
LOG_LEVEL = logging.DEBUG # Log level for application
STACK_SIM_THRESHOLD = 0.6 # Stacktrace similarity threshold to determine phase change
DATA_DIR = "/home/ubuntu/data" # Location of folder on workers where monitor.sh dumps data
STATS_FILE = "/sawcap_stats.txt"    # file to save reported accuracy values to
BATCH_SIZE = 3 # Number of profiles needed for a phase to train a model
NUM_RESOURCES = 2 # Number of resources; Currently - cpu, mem
ENABLE_STATS = True # Enable collection and printing of stats
ALGO = "lasso" # Defines prediction model
ANOMALY_DETECTION_ENABLED = True
LOCAL_DATA_DIR = "/home/ubuntu/data" # location on the runner where data should be stored
ORCHESTRATOR_PRIVATE_IP="192.168.0.3" # Used for metrics publishing
