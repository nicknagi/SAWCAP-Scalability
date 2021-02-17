#!/usr/bin/python3
import digitalocean
import argparse
import os
import time
from utils import add_hosts_entries, write_slaves_file_on_master, remove_hosts_entry, \
 run_hadoop, modify_bashrc_runner, modify_capstone_worker_configs_runner, update_capstone_repo, modify_spark_conf_runner, try_ssh, \
     modify_capstone_original_code_slaves_runner, modify_hibench_conf_runner, run_data_collection, start_monitoring, modify_num_iters_runner, \
         write_hadoop_configs, add_prometheus_conf_orchestrator
import logging
import sys
import multiprocessing as mp
import random

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
parser.add_argument("--workload_scale", type=str,
                    help="param to be set for workload size in hibench.conf", default="large")
parser.add_argument("--start_data_collection", help="start data collection script on cluster, also starts monitoring", type=str)
parser.add_argument("-e", "--extend", action="store_true", help="Extend an existing cluster instead of creating a new cluster")
args = parser.parse_args()

num_workers = args.numworkers
token = os.getenv("DIGITALOCEAN_ACCESS_TOKEN")

# Set the VM size depending on workload size
VM_SIZE="s-2vcpu-2gb"
if args.workload_scale == "large":
    VM_SIZE = "s-4vcpu-8gb"

REGION = "tor1"
WORKER_SNAPSHOT_ID = "77183076" # v3
RUNNER_SNAPSHOT_ID = "77183059"
MASTER_SNAPSHOT_ID = "77183051"
WORKER_SIZE = VM_SIZE
RUNNER_SIZE = "s-2vcpu-2gb"
MASTER_SIZE = "s-2vcpu-4gb"

name_suffix = str(int(time.time())) if args.uniqueid is None else args.uniqueid
master_name = "hadoop-master-" + name_suffix
runner_name = "runner-" + name_suffix
worker_names = [
    f"hadoop-worker-{name_suffix}-{x:02d}" for x in range(1, num_workers+1)]
manager = digitalocean.Manager(token=token)
keys = manager.get_all_sshkeys()

if args.workload_scale not in ["tiny", "small", "large"]:
    print("Invalid workload scale type!")
    sys.exit(1)

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

def droplet_ready(droplet):
    actions = droplet.get_actions()

    for action in actions:
        action.load()
        # Once it shows "completed", droplet is up and running
        if action.status != "completed":
            return False

    return True

def can_ssh(droplet):
    try:
        try_ssh(droplet.private_ip_address)
        return True
    except Exception:
        return False

def wait_until_droplet_ready(droplet):
    # Do a quick check first otherwise wait longer
    if droplet_ready(droplet) and can_ssh(droplet):
        return

    while not droplet_ready(droplet):
        logger.debug(f"Waiting for {droplet.name} to complete")
        time.sleep(5)

    logger.debug(f"{droplet.name} Completed")

    # Load latest droplet data
    while droplet.private_ip_address is None:
        droplet.load()
        time.sleep(1)

    # Droplet is only ready when we can ssh, at times it can be complete but not ready
    while not can_ssh(droplet):
        logger.debug(f"Waiting for {droplet.name} to be ready")
        time.sleep(2)

    logger.debug(f"{droplet.name} Ready!")

# Function to add tag to droplet, repeatedly tries until done
def add_tag_to_droplet(tag_name, droplet):
    tag_done = False
    while(tag_done is False):
        tag = digitalocean.Tag(token=token, name=tag_name)
        tag.add_droplets([droplet.id])
        time.sleep(1)

        droplet.load()
        if (tag_name in droplet.tags):
            tag_done = True
            logger.debug(f"Tag {tag_name} added succesfully to {droplet.name}")
        else:
            logger.debug(f"Tag {tag_name} not added succesfully to {droplet.name}, trying again")

# -----------------------------  Create all the droplets ---------------------------------------------

worker_droplets = []

if args.extend:
    my_droplets = manager.get_all_droplets()
    my_droplet_names = [d.name for d in my_droplets]
    
    try:
        master_droplet = my_droplets[my_droplet_names.index(master_name)]
        runnner_droplet = my_droplets[my_droplet_names.index(runner_name)]
    except ValueError as e:
        logger.error("No such cluster is found.")
        sys.exit(1)

    for i in range(1, 10000+1):
        worker_name = f"hadoop-worker-{name_suffix}-{i:02d}"
        try:
            droplet = my_droplets[my_droplet_names.index(worker_name)]
        except ValueError as e:
            break;
        worker_droplets.append(droplet)

else:
    runner_droplet = create_droplet(runner_name, RUNNER_SNAPSHOT_ID, RUNNER_SIZE)
    logger.info(f"Requested creation of {runner_droplet.name}")

    master_droplet = create_droplet(master_name, MASTER_SNAPSHOT_ID, MASTER_SIZE)
    logger.info(f"Requested creation of {master_droplet.name}")

    for worker_name in worker_names:
        logger.info(f"Requested creation of {worker_name}")
        worker_droplets.append(create_droplet(
            worker_name, WORKER_SNAPSHOT_ID, WORKER_SIZE))

print(master_droplet)
print(runner_droplet)
print(worker_droplet)
sys.exit(0)

# ---------------------------- Wait For Master To Complete ---------------------------------------------------

logger.info("Starting to wait for master to spin up")
wait_until_droplet_ready(master_droplet)
logger.info("Master has been spun up")

# Add tag to master
add_tag_to_droplet("hadoop-debug", master_droplet)

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

# Modify Hadoop configs on master
write_hadoop_configs(args.workload_scale, master_droplet.private_ip_address)
logger.info("Modified master Hadoop configs")

# ---------------------------- Modify Worker Files ---------------------------------------------------
def setup_worker(worker_droplet):
    logger.info(f"Starting to wait for worker {worker_droplet.name} to spin up")
    wait_until_droplet_ready(worker_droplet)
    logger.info(f"Worker {worker_droplet.name} has been spun up")
    
    # Add tag to workers
    add_tag_to_droplet("hadoop-debug", worker_droplet)

    # Modify worker /etc/hosts
    remove_hosts_entry(worker_droplet.name, worker_droplet.private_ip_address)
    lines_to_add_worker = [
        f"{master_droplet.private_ip_address} spark-master\n", *woker_hostnames_ip_lines]
    add_hosts_entries(lines_to_add_worker, worker_droplet.private_ip_address)
    logger.info(f"Modified {worker_droplet.name} /etc/hosts")

    # Update capstone repo
    update_capstone_repo(worker_droplet.private_ip_address)
    logger.info(f"Updated {worker_droplet.name} capstone repo")

    # Modify Hadoop Configs
    write_hadoop_configs(args.workload_scale, worker_droplet.private_ip_address)
    logger.info(f"Modified {worker_droplet.name} Hadoop Configs")

num_workers = 3
# Setup all workers
# Weird bug fix as per issue: https://bugs.python.org/issue35629
import contextlib
with contextlib.closing(mp.Pool(num_workers)) as pool:
    pool.map(setup_worker, worker_droplets)

# for worker_droplet in worker_droplets:
#     setup_worker(worker_droplet)

# ---------------------------- Run Hadoop On Master (Which starts workers as well) ---------------------------------------------------

# Start hadoop processes
logger.info(f"Starting Hadoop")
run_hadoop(master_droplet.private_ip_address)
logger.info(f"Hadoop Started")

# ---------------------------- Setup Runner ---------------------------------------------------

logger.info("Starting to wait for runner to spin up")
wait_until_droplet_ready(runner_droplet)
logger.info("Runner has been spun up")

# Refresh droplet data
runner_droplet.load()

# Add tag to runner
add_tag_to_droplet("hadoop-debug", runner_droplet)

# Modify worker /etc/hosts
lines_to_add_runner = [f"{master_droplet.private_ip_address} spark-master\n"]
add_hosts_entries(lines_to_add_runner, runner_droplet.private_ip_address)
logger.info("Modified runner /etc/hosts")

# Modify Hadoop Configs
write_hadoop_configs(args.workload_scale, runner_droplet.private_ip_address)
logger.info("Modified runner Hadoop Configs")

# Modify runner .bashrc
modify_bashrc_runner(runner_droplet.private_ip_address)
logger.info("Modified runner .bashrc")

# Update Capstone Repo
update_capstone_repo(runner_droplet.private_ip_address)
logger.info(f"Updated runner capstone repo")

# Modify capstone files
workers = [worker_droplet.private_ip_address for worker_droplet in worker_droplets]
modify_capstone_worker_configs_runner(runner_droplet.private_ip_address, workers)
modify_capstone_original_code_slaves_runner(runner_droplet.private_ip_address, workers)
logger.info("Modified runner config.py and servers in detect_anomaly.py")

# Modify spark.conf with num_executors = num_workers and hibench.conf with workload size
modify_spark_conf_runner(runner_droplet.private_ip_address, len(worker_droplets), args.workload_scale)
modify_hibench_conf_runner(runner_droplet.private_ip_address, args.workload_scale)
logger.info("Modified runner spark.conf and hibench.conf")

# -------------------------- Prometheus Setup -----------------------------------------

vm_ips = []

if master_droplet.private_ip_address is not None:
    vm_ips.append(master_droplet.private_ip_address)

if runner_droplet.private_ip_address is not None:
    vm_ips.append(runner_droplet.private_ip_address)

for worker in worker_droplets:
    vm_ips.append(worker.private_ip_address)

add_prometheus_conf_orchestrator(vm_ips, name_suffix)
logger.info("Modified prometheus config on orchestrator VM")
os.system("sudo service prometheus restart")
logger.info("Prometheus restarted")

# -------------------------- Data Collection ------------------------------------------

# Start data collection script
if args.start_data_collection is not None:
    for worker_droplet in worker_droplets:
        start_monitoring(worker_droplet.private_ip_address, 1)

    time.sleep(5)

    modify_num_iters_runner(runner_droplet.private_ip_address, args.start_data_collection)
    run_data_collection(runner_droplet.private_ip_address)


logger.info(f"Done setting up cluster! - hadoop ui: http://{master_droplet.ip_address}:8069")

# ---------------------------- DONE ---------------------------------------------------

end = time.time()
from datetime import timedelta
logger.info(f"Total Time Taken: {timedelta(seconds=end-start)}")
