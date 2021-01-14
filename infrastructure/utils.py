import os
import paramiko
import logging
import sys

username = "root"
port = 22

logger = logging.getLogger(__name__)
stdout_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(fmt="[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s",
                              datefmt='%d-%b-%y %H:%M:%S')
stdout_handler.setFormatter(formatter)
logger.addHandler(stdout_handler)
logger.setLevel(logging.DEBUG)

def read_file_via_sftp(private_ip, filename):
    host = private_ip
    transport = paramiko.Transport((host, port))

    mykey = paramiko.RSAKey.from_private_key_file("/home/ubuntu/.ssh/orchestrator")
    transport.connect(username = username, pkey = mykey)
    sftp = paramiko.SFTPClient.from_transport(transport)

    f = sftp.file(filename)
    data = f.readlines()

    f.close()
    sftp.close()
    transport.close()
    return data

def write_file_via_sftp(private_ip, filename, contents):
    host = private_ip
    transport = paramiko.Transport((host, port))

    mykey = paramiko.RSAKey.from_private_key_file("/home/ubuntu/.ssh/orchestrator")
    transport.connect(username = username, pkey = mykey)
    sftp = paramiko.SFTPClient.from_transport(transport)

    f = sftp.file(filename, "w+")
    f.writelines(contents)

    f.close()
    sftp.close()
    transport.close()

# edit the /etc/hosts file by adding entries in the private_ip machine.
# each element of entries list is a line to be added to the file
def add_hosts_entries(entries, private_ip):
    filename = "/etc/hosts"
    contents = read_file_via_sftp(private_ip, filename)
    contents.extend(entries)
    write_file_via_sftp(private_ip, filename, contents)

def remove_hosts_entry(hostname, private_ip):
    filename = "/etc/hosts"
    contents = read_file_via_sftp(private_ip, filename)
    new_contents = []
    hostname_with_spaces = f" {hostname}\n"
    for line in contents:
        if hostname_with_spaces not in line:
            new_contents.append(line)
    write_file_via_sftp(private_ip, filename, new_contents)

def write_slaves_file_on_master(contents, private_ip):
    write_file_via_sftp(private_ip, "/usr/local/hadoop/etc/hadoop/slaves", contents)

def _log_ssh_output(stdout, stderr):
    logger.debug(stdout.read().decode())
    logger.debug(stderr.read().decode())

def run_hadoop(master_private_ip):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=master_private_ip, username='ubuntu', key_filename='/home/ubuntu/.ssh/id_rsa')

    logger.debug("\n\n Output from starting Hadoop: \n")
    _, out, err = ssh.exec_command("/usr/local/hadoop/bin/hdfs namenode -format")
    _log_ssh_output(out, err)
    _, out, err = ssh.exec_command("/usr/local/hadoop/sbin/start-dfs.sh && /usr/local/hadoop/sbin/start-yarn.sh")
    _log_ssh_output(out, err)
    _, out, err = ssh.exec_command("/usr/local/hadoop/sbin/mr-jobhistory-daemon.sh start historyserver")
    _log_ssh_output(out, err)
    logger.debug("\n\n")
    ssh.close()


# Function dedicated to exporting SPARK_LOCAL_IP variable in bash rc
def modify_bashrc_runner(runner_private_ip):
    filename = "/home/ubuntu/.bashrc"
    contents = read_file_via_sftp(runner_private_ip, filename)

    keyword = "SPARK_LOCAL_IP"
    replacement = f"export SPARK_LOCAL_IP={runner_private_ip}\n"

    contents = _find_and_replace_line(keyword, replacement, contents)
    
    contents.append(f"export HIBENCH_WORKLOAD_DIR=/usr/local/HiBench/bin/workloads")

    # very hack way of getting env variables to start data collection script
    env_copy = contents[-20:]
    write_file_via_sftp(runner_private_ip, "/home/ubuntu/.environment_export", env_copy)
    
    write_file_via_sftp(runner_private_ip, filename, contents)

def modify_capstone_worker_configs_runner(runner_private_ip, workers):
    filename = "/home/ubuntu/capstone/sawcap/config.py"
    contents = read_file_via_sftp(runner_private_ip, filename)

    keyword = "WORKERS "
    replacement = f"WORKERS = {workers}\n"

    contents = _find_and_replace_line(keyword, replacement, contents)
    
    write_file_via_sftp(runner_private_ip, filename, contents)

def modify_capstone_original_code_slaves_runner(runner_private_ip, workers):
    filename = "/home/ubuntu/capstone/archive/original/master_code/detect_anomaly.py"
    contents = read_file_via_sftp(runner_private_ip, filename)

    keyword = "servers = "
    replacement = f"servers = {workers}\n"

    contents = _find_and_replace_line(keyword, replacement, contents)
    
    write_file_via_sftp(runner_private_ip, filename, contents)

def update_capstone_repo(private_ip):
    path = "/home/ubuntu/capstone"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=private_ip, username='ubuntu', key_filename='/home/ubuntu/.ssh/id_rsa')

    logger.debug("\n Output From Updating Github Repo: \n")
    _, out, err = ssh.exec_command(f"cd {path} && git stash && git checkout main && git pull")
    _log_ssh_output(out, err)

def start_monitoring(worker_private_ip, interval):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=worker_private_ip, username='ubuntu', key_filename='/home/ubuntu/.ssh/id_rsa')

    transport = ssh.get_transport()
    channel = transport.open_session()

    logger.info(f"\n\n Starting monitoring on worker ip: {worker_private_ip} \n")
    channel.exec_command(f"(cd /home/ubuntu/capstone/sawcap/runner && /usr/bin/bash monitor.sh {interval} > /dev/null 2>&1) &")

    ssh.close()

def stop_monitoring(worker_private_ip):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=worker_private_ip, username='ubuntu', key_filename='/home/ubuntu/.ssh/id_rsa')

    logger.info(f"Stopping monitoring on worker ip: {worker_private_ip}")
    _, out, err = ssh.exec_command('ps aux | grep "/usr/bin/bash monitor.sh *" | awk \'{print $2}\' | xargs kill -9')
    _log_ssh_output(out, err)

    ssh.close()

def modify_spark_conf_runner(runner_private_ip, num_workers):
    filename = "/usr/local/HiBench/conf/spark.conf"
    contents = read_file_via_sftp(runner_private_ip, filename)

    keyword = "hibench.yarn.executor.num"
    replacement = f"{keyword}     {num_workers}\n"

    contents = _find_and_replace_line(keyword, replacement, contents)
    
    write_file_via_sftp(runner_private_ip, filename, contents)

def modify_hibench_conf_runner(runner_private_ip, workload_scale):
    filename = "/usr/local/HiBench/conf/hibench.conf"
    contents = read_file_via_sftp(runner_private_ip, filename)

    keyword = "hibench.scale.profile"
    replacement = f"{keyword}     {workload_scale}\n"

    contents = _find_and_replace_line(keyword, replacement, contents)
    
    write_file_via_sftp(runner_private_ip, filename, contents)

def modify_num_iters_runner(runner_private_ip, num_iter):
    filename = "/home/ubuntu/capstone/scripts/run_sawcap_on_workloads.sh"
    contents = read_file_via_sftp(runner_private_ip, filename)

    keyword = "NUM_ITERS="
    replacement = f"{keyword}{num_iter}\n"

    contents = _find_and_replace_line(keyword, replacement, contents)
    
    write_file_via_sftp(runner_private_ip, filename, contents)

def run_data_collection(runner_private_ip):
    logger.info(f"Starting data collection script")
    command = "(. ./.environment_export; cd /home/ubuntu/capstone/scripts; /usr/bin/bash run_workloads_in_background.sh 1 > /dev/null 2>&1) &"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=runner_private_ip, username='ubuntu', key_filename='/home/ubuntu/.ssh/id_rsa')

    logger.info(f"Starting data collection on runner: {runner_private_ip}")
    _, out, err = ssh.exec_command(command)
    _log_ssh_output(out, err)

    ssh.close()


def _find_and_replace_line(search_keyword, replacement, contents):
    new_contents = []
    for line in contents:
        if search_keyword in line:
            new_contents.append(replacement)
        else:
            new_contents.append(line)
    if new_contents == contents:
        logger.warning(f"File already has the change for keyword: {search_keyword}")
    return new_contents

def try_ssh(droplet_private_ip):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=droplet_private_ip, username='ubuntu', key_filename='/home/ubuntu/.ssh/id_rsa')

    ssh.close()

if __name__ == "__main__":
    pass