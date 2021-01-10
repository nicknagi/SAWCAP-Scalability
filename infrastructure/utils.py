import os
import paramiko

username = "root"
port = 22

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

def run_hadoop(master_private_ip):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=master_private_ip, username='ubuntu', key_filename='/home/ubuntu/.ssh/id_rsa')

    stdin, out, err = ssh.exec_command("/usr/local/hadoop/bin/hdfs namenode -format")
    print(out.read().decode(), err.read().decode())
    stdin, out, err = ssh.exec_command("/usr/local/hadoop/sbin/start-dfs.sh && /usr/local/hadoop/sbin/start-yarn.sh")
    print(out.read().decode(), err.read().decode())
    stdin, out, err = ssh.exec_command("/usr/local/hadoop/sbin/mr-jobhistory-daemon.sh start historyserver")
    print(out.read().decode(), err.read().decode())
    ssh.close()