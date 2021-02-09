import sys
import psutil

PYTHON_SCRIPT_NAME_TO_MONITOR = "sawcap.py"
INTERVAL = 1

def get_process_pid():
    pid = -1
    for p in psutil.process_iter(["name", "pid", "cmdline"]):
        if PYTHON_SCRIPT_NAME_TO_MONITOR in p.info["cmdline"]:
            pid = p.info["pid"]
            break
    return pid

while True:
    data = {"cpu": None, "mem": None, "down": None, "up": None}
    process_pid = -1
    process = None

    for line in sys.stdin:
        if not psutil.pid_exists(process_pid):
            process_pid = get_process_pid()
            process = None if process_pid == -1 else psutil.Process(process_pid)

        if f"python3/{process_pid}" in line:
            data["down"] = float(line.split()[-1])
            data["up"] = float(line.split()[-2])
            data["cpu"] = process.cpu_percent()
            data["mem"] = process.memory_percent()
            print(data)