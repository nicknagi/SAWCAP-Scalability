import time
import subprocess
import os

def gather_profile():
    #ps aux|grep 'spark.executor.CoarseGrainedExecutorBackend'|head -1|awk '{print $2}'
    try:
        first = subprocess.Popen(('jps'), stdout=subprocess.PIPE) 
        pid = subprocess.check_output(('grep', 'CoarseGrainedExecutorBackend'),stdin=first.stdout).strip().split()[0].decode()
        
        #print(pid)        
        if(len(pid) > 0):
            os.system("./monitor.sh "+str(pid))
        else:
            os.system("./monitor.sh 0")
    except subprocess.CalledProcessError as e:
         os.system("./monitor.sh 0")

def monitor():
    while True:
        #start = time.clock()
        gather_profile()
        #end = time.clock()
        #print(f"Time taken for sampling: {end-start}")
        time.sleep(1)



if __name__ == '__main__':
    monitor()
