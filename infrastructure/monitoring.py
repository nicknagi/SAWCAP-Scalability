import argparse
import logging
import os
import sys

import digitalocean

from utils import start_monitoring, stop_monitoring

# Setup logging
logger = logging.getLogger(__name__)
stdout_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(fmt="[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s",
                              datefmt='%d-%b-%y %H:%M:%S')
stdout_handler.setFormatter(formatter)
logger.addHandler(stdout_handler)
logger.setLevel(logging.DEBUG)

parser = argparse.ArgumentParser(description='Get info')

parser.add_argument("--uniqueid", type=str,
                    help="id of the cluster used as suffix", required=True)
parser.add_argument("--stop", help="stop monitoring", action="store_true")
parser.add_argument("--interval", type=str,
                    help="frequency of sampling for monitor.sh", default=1)
args = parser.parse_args()

stop = args.stop
name_suffix = args.uniqueid
worker_names = [f"hadoop-worker-{name_suffix}-{x:02d}" for x in range(1, 10000 + 1)]

token = os.getenv("DIGITALOCEAN_ACCESS_TOKEN")
manager = digitalocean.Manager(token=token)
all_droplets = manager.get_all_droplets()

worker_droplets = []
for droplet in all_droplets:
    if droplet.name in worker_names:
        worker_droplets.append(droplet)

for worker_droplet in worker_droplets:
    logger.info(f"Starting monitoring on {worker_droplet.name}")
    if stop:
        stop_monitoring(worker_droplet.private_ip_address)
    else:
        start_monitoring(worker_droplet.private_ip_address, args.interval)

if stop:
    logger.info("Monitoring is stopped on all workers")
else:
    logger.info("Monitoring is enabled on all workers")
