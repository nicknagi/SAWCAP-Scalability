# edit the /etc/hosts file by adding an entry in the private_ip machine
def add_hosts_entry(entry, private_ip):
    pass

def remove_hosts_entry(hostname, private_ip):
    pass

import os
import paramiko

host = "192.168.0.4"
port = 22
transport = paramiko.Transport((host, port))
username = "root"
mykey = paramiko.RSAKey.from_private_key_file("/home/ubuntu/.ssh/orchestrator")
transport.connect(username = username, pkey = mykey)
sftp = paramiko.SFTPClient.from_transport(transport)
f = sftp.file("/etc/hosts")
print(f.readlines())
f.close()
sftp.close()
transport.close()
