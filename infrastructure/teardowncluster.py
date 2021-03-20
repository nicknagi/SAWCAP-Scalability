#!/usr/bin/python3
import argparse
import os

import digitalocean

from utils import remove_prometheus_conf_orchestrator
import backoff
import logging

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument("--uniqueid", type=str,
                    help="id of the cluster used as suffix", required=True)
parser.add_argument("--leave_runner",
                    help="destroy all VMs except runner; useful for debugging", action='store_true')
args = parser.parse_args()

token = os.getenv("DIGITALOCEAN_ACCESS_TOKEN")

REGION = "tor1"
WORKER_SNAPSHOT_ID = "76642056"
RUNNER_SNAPSHOT_ID = "76642032"
MASTER_SNAPSHOT_ID = "76642031"
WOKER_SIZE = "s-1vcpu-2gb"
RUNNER_SIZE = "s-2vcpu-2gb"
MASTER_SIZE = "s-2vcpu-2gb"

name_suffix = args.uniqueid
master_name = "hadoop-master-" + name_suffix
runner_name = "runner-" + name_suffix
worker_names = [f"hadoop-worker-{name_suffix}-{x:02d}" for x in range(1, 10000 + 1)]
droplets_to_remove = [master_name, runner_name, *worker_names]

if (args.leave_runner):
    droplets_to_remove.remove(runner_name)

# remove prometheus config
remove_prometheus_conf_orchestrator(name_suffix)
os.system("sudo service prometheus restart")
print("Removed prometheus configuration")

# Setup backoff library logger
logging.getLogger('backoff').addHandler(logging.StreamHandler(sys.stdout))

@backoff.on_exception(backoff.expo, digitalocean.DataReadError, max_time=300)
def remove_all_droplets():
    manager = digitalocean.Manager(token=token)
    my_droplets = manager.get_all_droplets()
    for droplet in my_droplets:
        if droplet.name in droplets_to_remove:
            droplet.destroy()
            print(f"Droplet {droplet.name} destroyed")

# Remove all droplets in cluster
remove_all_droplets()