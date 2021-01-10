import digitalocean
import argparse
import os
import time
from utils import add_hosts_entries, write_slaves_file_on_master, remove_hosts_entry, run_hadoop
import logging
import sys
import multiprocessing as mp

logger = logging.getLogger(__name__)
stdout_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(fmt=' %(asctime)s :: %(levelname)-8s -- %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S')
stdout_handler.setFormatter(formatter)
logger.addHandler(stdout_handler)
logger.setLevel(logging.DEBUG)

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument("-n", "--numworkers", type=int,
                    help="The number of workers in the hadoop cluster", required=True)
parser.add_argument("--uniqueid", type=str,
                    help="id of the cluster used as suffix")
args = parser.parse_args()

num_workers = args.numworkers
token = os.getenv("DIGITALOCEAN_ACCESS_TOKEN")

REGION="tor1"
WORKER_SNAPSHOT_ID="76642056"
RUNNER_SNAPSHOT_ID="76642032"
MASTER_SNAPSHOT_ID="76642031"
WOKER_SIZE="s-1vcpu-2gb"
RUNNER_SIZE="s-2vcpu-2gb"
MASTER_SIZE="s-2vcpu-2gb"

name_suffix = str(int(time.time())) if args.uniqueid is None else args.uniqueid
master_name = "hadoop-master-" + name_suffix
runner_name = "runner-" + name_suffix
worker_names = [f"hadoop-worker-{name_suffix}-{x:02d}" for x in range(1, num_workers+1)]
manager = digitalocean.Manager(token=token)
keys = manager.get_all_sshkeys()

# -----------------------------  Utility Functions ---------------------------------------------

def create_droplet(name, image, size):
    droplet = digitalocean.Droplet(token=token,
                                   name=name,
                                   region=REGION,
                                   image=image,
                                   size_slug=size,
                                   ssh_keys=keys
                                   )
    droplet.create()
    return droplet

def wait_until_droplet_up(droplet):
    actions = droplet.get_actions()
    complete = False
    while not complete:
        time.sleep(0.5)
        logger.debug(f"Waiting for {droplet.name} to complete")
        complete = True
        for action in actions:
            action.load()
            # Once it shows "completed", droplet is up and running
            if action.status != "completed":
                complete = False
    logger.debug(f"{droplet.name} Completed")
    time.sleep(30)

# -----------------------------  Create all the droplets ---------------------------------------------

# runner_droplet = create_droplet(runner_name, RUNNER_SNAPSHOT_ID, RUNNER_SIZE)     ---------- ENABLE LATER

master_droplet = create_droplet(master_name, MASTER_SNAPSHOT_ID, MASTER_SIZE)

worker_droplets = []
for worker_name in worker_names:
    worker_droplets.append(create_droplet(worker_name, WORKER_SNAPSHOT_ID, WOKER_SIZE))

# ---------------------------- Wait For Master To Complete ---------------------------------------------------

logger.info("Starting to wait for master to spin up")
wait_until_droplet_up(master_droplet)
logger.info("Master has been spun up")

# Add tag to master
tag = digitalocean.Tag(token=token, name="hadoop-debug")
tag.add_droplets([master_droplet.id])

# Refresh data about droplets
master_droplet.load()

# Ensure private ip available for all workers
done = False
while not done:
    done = True
    for worker_droplet in worker_droplets:
        worker_droplet.load()
        if worker_droplet.private_ip_address == None:
            done = False

# ---------------------------- Modify Master Files ---------------------------------------------------

worker_private_ips = [(worker_droplet.name, worker_droplet.private_ip_address) for worker_droplet in worker_droplets]
woker_hostnames_ip_lines = [f"{entry[1]} {entry[0]}\n" for entry in worker_private_ips]

lines_to_add_master = ["127.0.1.1 spark-master\n", *woker_hostnames_ip_lines]

# Modify master /etc/hosts
add_hosts_entries(lines_to_add_master, master_droplet.private_ip_address)
logger.info("Modified master /etc/hosts")

# Modify slaves file on master
worker_private_ips = [f"{worker_droplet.private_ip_address}\n" for worker_droplet in worker_droplets]
write_slaves_file_on_master(worker_private_ips, master_droplet.private_ip_address)
logger.info("Modified master slaves file")

# ---------------------------- Modify Worker Files ---------------------------------------------------
def setup_worker(worker_droplet):
    logger.info("Starting to wait for workers to spin up")
    wait_until_droplet_up(worker_droplet)
    logger.info(f"Worker {worker_droplet.name} has been spun up")

    # Add tag to workers
    tag = digitalocean.Tag(token=token, name="hadoop-debug")
    tag.add_droplets([worker_droplet.id])
    
    # Refresh worker droplet data
    worker_droplet.load()

    # Modify worker /etc/hosts
    remove_hosts_entry(worker_droplet.name, worker_droplet.private_ip_address)
    lines_to_add_worker = [f"{master_droplet.private_ip_address} spark-master\n", *woker_hostnames_ip_lines]
    add_hosts_entries(lines_to_add_worker, worker_droplet.private_ip_address)
    logger.info(f"Modified {worker_droplet.name} /etc/hosts")

# Setup all workers
with mp.Pool(4) as pool:
    pool.map(setup_worker, worker_droplets)

# ---------------------------- Run Hadoop ---------------------------------------------------

# Start hadoop processes
logger.info(f"Starting Hadoop")
run_hadoop(master_droplet.private_ip_address)
logger.info(f"Hadoop Started")

# ---------------------------- Setup Runner ---------------------------------------------------
# TODO:  setup runner, pull github and change branch
