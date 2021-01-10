import digitalocean
import argparse
import os
import time

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

runner_droplet = create_droplet(runner_name, RUNNER_SNAPSHOT_ID, RUNNER_SIZE)

master_droplet = create_droplet(master_name, MASTER_SNAPSHOT_ID, MASTER_SIZE)

worker_droplets = []
for worker_name in worker_names:
    worker_droplets.append(create_droplet(worker_name, WORKER_SNAPSHOT_ID, WOKER_SIZE))

worker_private_ips = [(worker_droplet.name, worker_droplet.private_ip_address) for worker_droplet in worker_droplets]
print(worker_private_ips)


