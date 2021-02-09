import sys
import psutil

PYTHON_SCRIPT_NAME_TO_MONITOR = "/home/ubuntu/capstone/sawcap/sawcap.py"

# Returns the pid of the script we want - PYTHON_SCRIPT_NAME_TO_MONITOR
def get_process_pid():
    pid = -1
    for p in psutil.process_iter(["name", "pid", "cmdline"]):
        if PYTHON_SCRIPT_NAME_TO_MONITOR in p.info["cmdline"]:
            pid = p.info["pid"]
            break
    return pid

# Given a chunk of nethogs data, gets resource usage data i.e. network, cpu and memory
def get_resource_usage_data(nethogs_data):
    data = {"cpu": 0, "mem": 0, "download": 0, "upload": 0}
    procs_under_consideration = []

    main_pid = get_process_pid()
    main_proccess = None if main_pid == -1 else psutil.Process(main_pid)

    if main_proccess is None:
        return

    procs_under_consideration.append(main_pid)
    children = main_proccess.children(recursive=True)
    for child in children:
        procs_under_consideration.append(child.pid)

    for line in nethogs_data:
        if len(line.split()) < 3:
            continue
        
        # Sawcap created ssh connections to read data from workers
        if f"ssh/" in line.split()[0]:
            data["upload"] += float(line.split()[1])
            data["download"] += float(line.split()[2])
            continue
        
        # collect data from any child processes that sawcap might have created
        for proc in procs_under_consideration:
            if f"{proc}" in line.split()[0]:
                data["upload"] += float(line.split()[1])
                data["download"] += float(line.split()[2])
                data["mem"] += psutil.Process(proc).memory_percent()
                data["cpu"] += psutil.Process(proc).cpu_percent(interval=0.1)
                break

    return data

# stdin: data from running nethogs, for example running "sudo nethogs -t -d 1 | python3 sawcap_resource_monitor.py"
while True:
    chunk = []
    for line in sys.stdin:
        if line == "Refreshing:\n":           
            print(get_resource_usage_data(chunk))
            chunk = []
        else:
            chunk.append(line)