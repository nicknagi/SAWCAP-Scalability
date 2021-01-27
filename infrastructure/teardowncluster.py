#!/usr/bin/python3
import digitalocean
import argparse
import os
from utils import remove_prometheus_conf_orchestrator

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument("--uniqueid", type=str,
                    help="id of the cluster used as suffix", required=True)
args = parser.parse_args()

token = os.getenv("DIGITALOCEAN_ACCESS_TOKEN")

REGION="tor1"
WORKER_SNAPSHOT_ID="76642056"
RUNNER_SNAPSHOT_ID="76642032"
MASTER_SNAPSHOT_ID="76642031"
WOKER_SIZE="s-1vcpu-2gb"
RUNNER_SIZE="s-2vcpu-2gb"
MASTER_SIZE="s-2vcpu-2gb"

name_suffix = args.uniqueid
master_name = "hadoop-master-" + name_suffix
runner_name = "runner-" + name_suffix
worker_names = [f"hadoop-worker-{name_suffix}-{x:02d}" for x in range(1, 10000+1)]
names = [master_name, runner_name, *worker_names]

# remove prometheus config
remove_prometheus_conf_orchestrator(name_suffix)

manager = digitalocean.Manager(token=token)
my_droplets = manager.get_all_droplets()
for droplet in my_droplets:
    if droplet.name in names:
        droplet.destroy()
        print(f"Droplet {droplet.name} destroyed")

