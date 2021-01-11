import digitalocean
import argparse
import os
import time
from utils import add_hosts_entries, write_slaves_file_on_master, remove_hosts_entry, run_hadoop, modify_bashrc_runner, modify_capstone_worker_configs_runner, update_capstone_repo
import logging
import sys
import multiprocessing as mp

# Profiling
start = time.time()

logger = logging.getLogger(__name__)
stdout_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(fmt="[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s",
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

REGION = "tor1"
WORKER_SNAPSHOT_ID = "76642056"
RUNNER_SNAPSHOT_ID = "76642032"
MASTER_SNAPSHOT_ID = "76642031"
WORKER_SIZE = "s-1vcpu-2gb"
RUNNER_SIZE = "s-2vcpu-2gb"
MASTER_SIZE = "s-2vcpu-2gb"

name_suffix = str(int(time.time())) if args.uniqueid is None else args.uniqueid
master_name = "hadoop-master-" + name_suffix
runner_name = "runner-" + name_suffix
worker_names = [
    f"hadoop-worker-{name_suffix}-{x:02d}" for x in range(1, num_workers+1)]
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
        time.sleep(2)
        logger.debug(f"Waiting for {droplet.name} to complete")
        complete = True
        for action in actions:
            action.load()
            # Once it shows "completed", droplet is up and running
            if action.status != "completed":
                complete = False

    logger.debug(f"{droplet.name} Completed")

    #Wait for machine to actually boot up
    time.sleep(30) 

# -----------------------------  Create all the droplets ---------------------------------------------


runner_droplet = create_droplet(runner_name, RUNNER_SNAPSHOT_ID, RUNNER_SIZE)

master_droplet = create_droplet(master_name, MASTER_SNAPSHOT_ID, MASTER_SIZE)

worker_droplets = []
for worker_name in worker_names:
    worker_droplets.append(create_droplet(
        worker_name, WORKER_SNAPSHOT_ID, WORKER_SIZE))

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

worker_private_ips = [(worker_droplet.name, worker_droplet.private_ip_address)
                      for worker_droplet in worker_droplets]
woker_hostnames_ip_lines = [
    f"{entry[1]} {entry[0]}\n" for entry in worker_private_ips]

lines_to_add_master = ["127.0.1.1 spark-master\n", *woker_hostnames_ip_lines]

# Modify master /etc/hosts
add_hosts_entries(lines_to_add_master, master_droplet.private_ip_address)
logger.info("Modified master /etc/hosts")

# Modify slaves file on master
worker_private_ips = [
    f"{worker_droplet.private_ip_address}\n" for worker_droplet in worker_droplets]
write_slaves_file_on_master(
    worker_private_ips, master_droplet.private_ip_address)
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
    lines_to_add_worker = [
        f"{master_droplet.private_ip_address} spark-master\n", *woker_hostnames_ip_lines]
    add_hosts_entries(lines_to_add_worker, worker_droplet.private_ip_address)
    logger.info(f"Modified {worker_droplet.name} /etc/hosts")

    # Update capstone repo
    update_capstone_repo(worker_droplet.private_ip_address)
    logger.info(f"Updated {worker_droplet.name} capstone repo")

num_workers = min(len(worker_droplets), 50)
# Setup all workers
with mp.Pool(num_workers) as pool:
    pool.map(setup_worker, worker_droplets)

# ---------------------------- Run Hadoop On Master (Which starts workers as well) ---------------------------------------------------

# Start hadoop processes
logger.info(f"Starting Hadoop")
run_hadoop(master_droplet.private_ip_address)
logger.info(f"Hadoop Started")

# ---------------------------- Setup Runner ---------------------------------------------------

logger.info("Starting to wait for runner to spin up")
wait_until_droplet_up(runner_droplet)
logger.info("Runner has been spun up")

# Refresh droplet data
runner_droplet.load()

# Add tag to runner
tag = digitalocean.Tag(token=token, name="hadoop-debug")
tag.add_droplets([runner_droplet.id])

# Modify worker /etc/hosts
lines_to_add_runner = [f"{master_droplet.private_ip_address} spark-master\n"]
add_hosts_entries(lines_to_add_runner, runner_droplet.private_ip_address)
logger.info("Modified runner /etc/hosts")

# Modify runner .bashrc
modify_bashrc_runner(runner_droplet.private_ip_address)
logger.info("Modified runner .bashrc")

# Update Capstone Repo
update_capstone_repo(runner_droplet.private_ip_address)
logger.info(f"Updated runner capstone repo")

# Modify capstone files
workers = [worker_droplet.private_ip_address for worker_droplet in worker_droplets]
modify_capstone_worker_configs_runner(runner_droplet.private_ip_address, workers)
logger.info("Modified runner config.py")

logger.info(f"Done setting up cluster! - hadoop ui: http://{master_droplet.ip_address}:8069")

# ---------------------------- DONE ---------------------------------------------------

end = time.time()
from datetime import timedelta
logger.info(f"Total Time Taken: {timedelta(seconds=end-start)}")