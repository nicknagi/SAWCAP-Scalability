#!/usr/bin/python3
import argparse
import logging
import multiprocessing as mp
import os
import sys
import time
from datetime import timedelta
import contextlib

import digitalocean
import backoff

from utils import add_hosts_entries, write_slaves_file_on_master, remove_hosts_entry, \
    run_hadoop, modify_bashrc_runner, modify_capstone_configs_file_on_runner, update_capstone_repo, \
    modify_spark_conf_runner, try_ssh, \
    modify_capstone_original_code_slaves_runner, modify_hibench_conf_runner, run_data_collection, start_monitoring, \
    modify_num_iters_runner, \
    write_hadoop_configs, add_prometheus_conf_orchestrator, run_sawcap_monitoring, remove_prometheus_conf_orchestrator

# Profiling
start = time.time()

logger = logging.getLogger(__name__)
stdout_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(fmt="[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s",
                              datefmt='%d-%b-%y %H:%M:%S')
stdout_handler.setFormatter(formatter)
logger.addHandler(stdout_handler)
logger.setLevel(logging.DEBUG)

# Setup backoff library logger
logging.getLogger('backoff').addHandler(logging.StreamHandler(sys.stdout))

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument("-n", "--numworkers", type=int,
                    help="The number of workers in the hadoop cluster", required=True)
parser.add_argument("--uniqueid", type=str,
                    help="id of the cluster used as suffix")
parser.add_argument("--workload_scale", type=str,
                    help="param to be set for workload size in hibench.conf", default="large")
parser.add_argument("--git_branch", type=str,
                    help="branch to be cloned on all machines in cluster", default="main")
parser.add_argument("--start_data_collection", help="start data collection script on cluster, also starts monitoring",
                    type=str)
parser.add_argument("-e", "--extend", action="store_true", help="Extend an existing cluster instead of creating a new "
                                                                "cluster.")
parser.add_argument("--experiment_name", type=str,
                    help="Name of the experiment to be run", default="default-experiment")
parser.add_argument("-roc", "--run_original_code", action="store_true", help="Run the original code", default=False)
parser_arguments = parser.parse_args()

num_workers = parser_arguments.numworkers
token = os.getenv("DIGITALOCEAN_ACCESS_TOKEN")

# Set the VM size depending on workload size
VM_SIZE = "s-2vcpu-2gb"
if parser_arguments.workload_scale in ["large", "huge"]:
    VM_SIZE = "s-4vcpu-8gb"

REGION = "tor1"
WORKER_SNAPSHOT_ID = "79959117"  # v3
RUNNER_SNAPSHOT_ID = "77183059"
MASTER_SNAPSHOT_ID = "77183051"
WORKER_SIZE = VM_SIZE
RUNNER_SIZE = "s-2vcpu-2gb"
MASTER_SIZE = "s-2vcpu-4gb"

name_suffix = str(int(time.time())) if parser_arguments.uniqueid is None else parser_arguments.uniqueid
master_name = "hadoop-master-" + name_suffix
runner_name = "runner-" + name_suffix
worker_names = [
    f"hadoop-worker-{name_suffix}-{x:02d}" for x in range(1, parser_arguments.numworkers + 1)]
manager = digitalocean.Manager(token=token)
keys = manager.get_all_sshkeys()

if parser_arguments.workload_scale not in ["tiny", "small", "large", "huge"]:
    print("Invalid workload scale type!")
    sys.exit(1)

# -----------------------------  Utility Functions ---------------------------------------------


def backoff_hdlr(details):
    wait = details["wait"]
    args = details["args"]
    kwargs = details["kwargs"]
    tries = details["tries"]
    logger.info(f"Backing off {wait:0.1f} seconds afters {tries} tries "
           f"calling function {args[0].__name__} with args {args[1:]} and kwargs "
           f"{kwargs}")

# Function used to wrap any digitalocean API calls to implement backoff when too many API requests
@backoff.on_exception(backoff.expo, digitalocean.DataReadError, max_time=300, on_backoff=backoff_hdlr)
def wrap_digitalocean_call(func, *args, **kwargs):
    return func(*args, **kwargs)


def _create_droplet(droplet_to_create):
    droplet_to_create.create()


def create_droplet(name, image, size):
    droplet_created = digitalocean.Droplet(token=token,
                                           name=name,
                                           region=REGION,
                                           image=image,
                                           size_slug=size,
                                           ssh_keys=keys
                                           )
    wrap_digitalocean_call(_create_droplet, droplet_created)
    return droplet_created


def get_actions_for_droplet(droplet_to_get_actions):
    return droplet_to_get_actions.get_actions()


def load_action(action):
    action.load()


def load_droplet(droplet_to_load):
    droplet_to_load.load()


def droplet_ready(droplet_to_be_ready):
    actions = wrap_digitalocean_call(get_actions_for_droplet, droplet_to_be_ready)

    for action in actions:
        wrap_digitalocean_call(load_action, action)
        # Once it shows "completed", droplet is up and running
        if action.status != "completed":
            return False

    return True


def can_ssh(droplet_to_ssh):
    try:
        try_ssh(droplet_to_ssh.private_ip_address)
        return True
    except Exception:
        return False


def wait_until_droplet_ready(_droplet):
    # Do a quick check first otherwise wait longer
    if droplet_ready(_droplet) and can_ssh(_droplet):
        return

    while not droplet_ready(_droplet):
        logger.debug(f"Waiting for {_droplet.name} to complete")
        time.sleep(5)

    logger.debug(f"{_droplet.name} Completed")

    # Load latest droplet data
    while _droplet.private_ip_address is None:
        wrap_digitalocean_call(load_droplet, _droplet)
        time.sleep(1)

    # Droplet is only ready when we can ssh, at times it can be complete but not ready
    while not can_ssh(_droplet):
        logger.debug(f"Waiting for {_droplet.name} to be ready")
        time.sleep(2)

    logger.debug(f"{_droplet.name} Ready!")


# Function to add tag to droplet, repeatedly tries until done
def add_tag_to_droplet(tag_name, droplet_to_add_tag):
    tag_done = False
    while tag_done is False:
        tag = digitalocean.Tag(token=token, name=tag_name)
        tag.add_droplets([droplet_to_add_tag.id])
        time.sleep(1)

        wrap_digitalocean_call(load_droplet, droplet_to_add_tag)
        if tag_name in droplet_to_add_tag.tags:
            tag_done = True
            logger.debug(f"Tag {tag_name} added succesfully to {droplet_to_add_tag.name}")
        else:
            logger.debug(f"Tag {tag_name} not added succesfully to {droplet_to_add_tag.name}, trying again")


def get_all_droplets():
    return manager.get_all_droplets()


# -----------------------------  Create all the droplets ---------------------------------------------

new_worker_droplets = []
existing_worker_droplets = []
worker_droplets = []
new_num_workers = parser_arguments.numworkers
existing_num_workers = 0

if parser_arguments.extend:
    my_droplets = wrap_digitalocean_call(get_all_droplets)
    my_droplet_names = [d.name for d in my_droplets]

    try:
        master_droplet = my_droplets[my_droplet_names.index(master_name)]
        runner_droplet = my_droplets[my_droplet_names.index(runner_name)]
    except ValueError as e:
        logger.error("No such cluster is found.")
        sys.exit(1)

    for existing_num_workers in range(1, 10000 + 1):
        worker_name = f"hadoop-worker-{name_suffix}-{existing_num_workers:02d}"
        try:
            droplet = my_droplets[my_droplet_names.index(worker_name)]
        except ValueError as e:
            break
        existing_worker_droplets.append(droplet)
        worker_droplets.append(droplet)
    existing_num_workers -= 1
    logger.info(f"Existing Master: {master_droplet}")
    logger.info(f"Existing Runner: {runner_droplet}")
    logger.info(f"Existing Worker #: {existing_num_workers}")
    input("Press any key to continue...")

else:
    runner_droplet = create_droplet(runner_name, RUNNER_SNAPSHOT_ID, RUNNER_SIZE)
    logger.info(f"Requested creation of {runner_droplet.name}")

    master_droplet = create_droplet(master_name, MASTER_SNAPSHOT_ID, MASTER_SIZE)
    logger.info(f"Requested creation of {master_droplet.name}")

worker_names = [
    f"hadoop-worker-{name_suffix}-{x:02d}" for x in
    range(existing_num_workers + 1, new_num_workers + existing_num_workers + 1)]

for worker_name in worker_names:
    logger.info(f"Requested creation of {worker_name}")
    d = create_droplet(worker_name, WORKER_SNAPSHOT_ID, WORKER_SIZE)
    new_worker_droplets.append(d)
    worker_droplets.append(d)


# ---------------------------- If extend, reinitialize all nodes ---------------------------------------------


def restore_droplet(droplet_to_restore, snapshot_id):
    droplet_to_restore.restore(snapshot_id)


if parser_arguments.extend:
    for worker_droplet in existing_worker_droplets:
        logger.info(f"Requested reinitialization of {worker_droplet.name}")
        wrap_digitalocean_call(restore_droplet, worker_droplet, WORKER_SNAPSHOT_ID)

    wrap_digitalocean_call(restore_droplet, runner_droplet, RUNNER_SNAPSHOT_ID)
    logger.info(f"Requested reinitialization of {runner_droplet.name}")
    wrap_digitalocean_call(restore_droplet, master_droplet, MASTER_SNAPSHOT_ID)
    logger.info(f"Requested reinitialization of {master_droplet.name}")

# ---------------------------- Wait For Master To Complete ---------------------------------------------------

logger.info("Starting to wait for master to spin up")
wait_until_droplet_ready(master_droplet)
logger.info("Master has been spun up")

# Add tag to master
wrap_digitalocean_call(add_tag_to_droplet, "hadoop-debug", master_droplet)

# Refresh data about droplets
wrap_digitalocean_call(load_droplet, master_droplet)

# Ensure private ip available for all workers
done = False
while not done:
    done = True
    for worker_droplet in worker_droplets:
        wrap_digitalocean_call(load_droplet, worker_droplet)
        if worker_droplet.private_ip_address is None:
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
write_hadoop_configs(parser_arguments.workload_scale, master_droplet.private_ip_address)
logger.info("Modified master Hadoop configs")


# ---------------------------- Modify Worker Files ---------------------------------------------------
def setup_worker(worker_droplet_to_setup):
    logger.info(f"Starting to wait for worker {worker_droplet_to_setup.name} to spin up")
    wait_until_droplet_ready(worker_droplet_to_setup)
    logger.info(f"Worker {worker_droplet_to_setup.name} has been spun up")

    # Add tag to workers
    wrap_digitalocean_call(add_tag_to_droplet, "hadoop-debug", worker_droplet_to_setup)

    # Modify worker /etc/hosts
    remove_hosts_entry(worker_droplet_to_setup.name, worker_droplet_to_setup.private_ip_address)
    lines_to_add_worker = [
        f"{master_droplet.private_ip_address} spark-master\n", *woker_hostnames_ip_lines]
    add_hosts_entries(lines_to_add_worker, worker_droplet_to_setup.private_ip_address)
    logger.info(f"Modified {worker_droplet_to_setup.name} /etc/hosts")

    # Update capstone repo
    update_capstone_repo(worker_droplet_to_setup.private_ip_address, parser_arguments.git_branch)
    logger.info(f"Updated {worker_droplet_to_setup.name} capstone repo")

    # Modify Hadoop Configs
    write_hadoop_configs(parser_arguments.workload_scale, worker_droplet_to_setup.private_ip_address)
    logger.info(f"Modified {worker_droplet_to_setup.name} Hadoop Configs")


batch_size = min(len(worker_droplets), 10)
# Setup all workers
# Weird bug fix as per issue: https://bugs.python.org/issue35629
with contextlib.closing(mp.Pool(batch_size)) as pool:
    pool.map(setup_worker, worker_droplets)

# ---------------------------- Run Hadoop On Master (Which starts workers as well) -------------------------------------

# Start hadoop processes
logger.info(f"Starting Hadoop")
run_hadoop(master_droplet.private_ip_address)
logger.info(f"Hadoop Started")

# ---------------------------- Setup Runner ---------------------------------------------------

logger.info("Starting to wait for runner to spin up")
wait_until_droplet_ready(runner_droplet)
logger.info("Runner has been spun up")

# Refresh droplet data
wrap_digitalocean_call(load_droplet, runner_droplet)

# Add tag to runner
wrap_digitalocean_call(add_tag_to_droplet, "hadoop-debug", runner_droplet)

# Modify worker /etc/hosts
lines_to_add_runner = [f"{master_droplet.private_ip_address} spark-master\n"]
add_hosts_entries(lines_to_add_runner, runner_droplet.private_ip_address)
logger.info("Modified runner /etc/hosts")

# Modify Hadoop Configs
write_hadoop_configs(parser_arguments.workload_scale, runner_droplet.private_ip_address)
logger.info("Modified runner Hadoop Configs")

# Modify runner .bashrc
modify_bashrc_runner(runner_droplet.private_ip_address)
logger.info("Modified runner .bashrc")

# Update Capstone Repo
update_capstone_repo(runner_droplet.private_ip_address, parser_arguments.git_branch)
logger.info(f"Updated runner capstone repo")

# Modify capstone files
workers = [worker_droplet.private_ip_address for worker_droplet in worker_droplets]
modify_capstone_configs_file_on_runner(runner_droplet.private_ip_address, workers, parser_arguments.experiment_name)
modify_capstone_original_code_slaves_runner(runner_droplet.private_ip_address, workers)
logger.info("Modified runner config.py and servers in detect_anomaly.py")

# Modify spark.conf with num_executors = num_workers and hibench.conf with workload size
modify_spark_conf_runner(runner_droplet.private_ip_address, len(worker_droplets), parser_arguments.workload_scale)
modify_hibench_conf_runner(runner_droplet.private_ip_address, parser_arguments.workload_scale)
logger.info("Modified runner spark.conf and hibench.conf")

# Start sawcap resources monitoring
run_sawcap_monitoring(runner_droplet.private_ip_address)
logger.info("Started sawcap resource monitoring script")

# -------------------------- Prometheus Setup -----------------------------------------

vm_ips = []

if master_droplet.private_ip_address is not None:
    vm_ips.append(master_droplet.private_ip_address)

if runner_droplet.private_ip_address is not None:
    vm_ips.append(runner_droplet.private_ip_address)

for worker in new_worker_droplets:
    vm_ips.append(worker.private_ip_address)

for worker in existing_worker_droplets:
    vm_ips.append(worker.private_ip_address)

remove_prometheus_conf_orchestrator(name_suffix)
add_prometheus_conf_orchestrator(vm_ips, name_suffix)
logger.info("Modified prometheus config on orchestrator VM")
os.system("sudo service prometheus restart")
logger.info("Prometheus restarted")

# -------------------------- Data Collection ------------------------------------------

# Start data collection script
if parser_arguments.start_data_collection is not None:
    for worker_droplet in worker_droplets:
        start_monitoring(worker_droplet.private_ip_address, 1)

    time.sleep(5)

    modify_num_iters_runner(runner_droplet.private_ip_address, parser_arguments.start_data_collection)
    run_data_collection(runner_droplet.private_ip_address, parser_arguments.run_original_code)

logger.info(f"Done setting up cluster! - hadoop ui: http://{master_droplet.ip_address}:8069")

# ---------------------------- DONE ---------------------------------------------------

end = time.time()
logger.info(f"Total Time Taken: {timedelta(seconds=end - start)}")
