import time
import os
import pickle
from signal import signal, SIGINT
from sys import exit
import sys
from sklearn import linear_model
import numpy as np
import subprocess

servers = ['172.31.15.58', '172.31.1.111']
interval = 2  # interval to determine phase change

# structure of phase database
# {<key1, val1>, <key2, val2> ...}
# key => phase name (a string representation of the stacktrace functions)
# val =>
# {"temp_data":[ [[cpu_p1, cpu_p2, cpu_c], [mem_p1, mem_p2, mem_c], ..], <-prof1
#                [[cpu_p1, cpu_p2, cpu_c], [mem_p1, mem_p2, mem_c], ..], <-prof2
#                               .......
#                [[cpu_p1, cpu_p2, cpu_c], [mem_p1, mem_p2, mem_c], ..]]<-prof10
#
#           "models":[mod_cpu, mod_mem]}
#
# The "temp_data" is used for batched model update, we only update model after
# buffering 10 profiling points

phase_database = {}
num_resources = 2 # currently support CPU and memory

# prediction algorithm to use, "simple" works pretty well
algo = sys.argv[1]

# batch size for model update
batch_size = 3

# state machine for detecting anomaly
anom_confidence = 0

# we use the resource usage of prev 2 phases for building the machine learning
# model.  These are the meta-inputs
prev1_resource = []
prev2_resource = []

cur_phase = ""


def handler(signal_received, frame):
    # Handle any cleanup here
    print('Exiting after saving the current database')
    with open('/home/ubuntu/data/phase_db_' + algo, 'wb') as f:
        pickle.dump(phase_database, f)
    exit(0)

def predict_naive(cur_phase):
    return prev1_resource

def predict_agg(cur_phase):
    # get the models.  Number of models should be the number of resources
    models = phase_database[cur_phase]["models"]
    if len(models) == 0:
        # no models so far, just return the naive result
        return prev1_resource
    else:
        # make prediction for each model
        try:
            predictions = []
            for i in range(len(models)):
                pred = models[i]
                # prediction is returned as a 1D Array
                predictions.append(pred)
            # check if something went wrong
            if any(predictions):
                return predictions
            else:
                return prev1_resource
        except Exception as e:
            print("Probably not fitted model", e)
            return prev1_resource


def prediction_helper(cur_phase):
    if algo == "agg":
        return predict_agg(cur_phase)


def get_prediction(cur_phase):
    # if no phase available
    if cur_phase == "":
        return [0] * num_resources
    # if not there yet
    if cur_phase not in phase_database:
        return prev1_resource, "unseen"
    # if no model has been built yet, just use naive prediction
    if len(phase_database[cur_phase]["models"]) == 0:
        return prev1_resource, "seen"
    else:
        return prediction_helper(cur_phase), "seen"


def parse_resource_agg(file):
    # takes an input file which has one line per server for CPU and Mem
    # returns an aggregate of three
    lines = []
    with open(file) as f:
        lines = f.readlines()

    # Timeout heuristics
    if len(lines) != len(servers):
        print("Anomaly Detected.  The following is the stacktrace ")
        print(cur_phase)
        with open('/home/ubuntu/data/phase_db_' + algo, 'wb') as f:
            pickle.dump(phase_database, f)
        sys.exit(0)
    # process line by line
    resource_usage = [0] * len(lines[0].split(','))
    # print("Number of resources ", resource_usage)
    for line in lines:
        usages = line.split(',')
        for i in range(len(usages)):
            resource_usage[i] += float(usages[i])

    resource_usage = [float(i) / len(servers) for i in resource_usage]

    return resource_usage

def stacktrace_helper():
    # this function connects to the servers, fetches the threaddump, aggregates
    # them and extract threaddump and resource usage information from them
    # returns a list containing the threaddump and resource info

    # clear the prev buffer
    os.system("> ./threaddump_agg")
    os.system("> ./resource_agg")

    # fetch new data
    for s in servers:
        # accumulate threaddumps
        # When anomaly is run in any of the slaves, ssh also takes longer, so the timeout heuristics
        # is simple but powerful to detect those anomalies, though the timeout value should change
        # system to system
        command = "timeout --foreground 10 ssh -q -t " + s + " 'cat /home/ubuntu/data/threaddump_data' " \
                                     ">> ./threaddump_agg"
        os.system(command)
        # accumulate resource usage
        command = "timeout --foreground 10 ssh -q -t " + s + " 'cat /home/ubuntu/data/resource_data' " \
                                     ">> ./resource_agg"
        os.system(command)

    functions = []
    with open("./threaddump_agg") as f:
        functions = f.readlines()

    resource_agg = parse_resource_agg("./resource_agg")
    functions = [i.strip() for i in functions]

    return [set(functions), resource_agg]


def detect_phase_change(old_trace, cur_trace):
    # phase change is detected by comparing the set of functions between
    # the current timestamp with the previous timestamp

    # calculate stack_sim
    # if no functions in both sets, it is idle phase
    if len(old_trace) == 0 and len(cur_trace) == 0:
        return False

    # here, at least one of them !=0 elements
    divisor = max(len(old_trace), len(cur_trace))

    stack_sim = len(old_trace.intersection(cur_trace)) / float(divisor)

    stack_sim_threshold = 0.6

    # print("stack_sim ", stack_sim)
    if stack_sim < stack_sim_threshold:
        return True
    else:
        return False


def form_phase_string(old_trace, cur_trace, changed):
    # create phase_string based on phase change or not.
    # if no phase change, then only put the intersection
    # else put the current trace
    comm_funcs = old_trace.intersection(cur_trace)
    if changed:
        comm_funcs = cur_trace
    phase_string = ""
    for func in comm_funcs:
        phase_string += str(func) + "->"

    return phase_string


def add_models(cur_phase, cur_res):
    global phase_database
    for res in cur_res:
        if algo == 'agg':
            phase_database[cur_phase]["models"].append(0)


def add_profile(cur_phase, prev2_res, prev1_res, cur_res):
    global phase_database

    # get the number of resources
    num_res = len(cur_res)

    res_temp = []
    for r in range(num_res):
        res_temp.append([prev2_res[r], prev1_res[r], cur_res[r]])

    # print("Res temp ", res_temp)
    phase_database[cur_phase]["temp_data"].append(res_temp)


def format_data(cur_phase, res_index):
    # format data from the temporary profile collected
    # res_index tells the resource we are modeling for e.g. CPU or memory
    temp_data = phase_database[cur_phase]["temp_data"]
    X = []
    Y = []
    for i in range(batch_size):
        # loop through all the profiling points
        X.append([temp_data[i][res_index][0], temp_data[i][res_index][1]])
        Y.append(temp_data[i][res_index][2])
    return X, Y

def update_agg(cur_phase):
    # update using the batch of data
    global phase_database

    # do it for individual resources
    for i in range(len(prev1_resource)):
        X, Y = format_data(cur_phase, i)
        # print("Resource ", X, Y)
        flatten = lambda l: [item for sublist in l for item in sublist]
        X = flatten(X)
        # Aggregate with previous aggregate stored
        X.append(phase_database[cur_phase]["models"][i])
        phase_database[cur_phase]["models"][i] = np.average(X)


def update_helper(cur_phase):
    # update ML model for the batch collected
    if algo == "simple":
        pass
    elif algo == "agg":
        update_agg(cur_phase)


def update_ml_model(phase_string):
    # do not build model for an idle phase (no trace string)
    if phase_string == "":
        return
    global phase_database
    print("updating the model", hash(phase_string))
    # print(phase_database[phase_string]["temp_data"])
    update_helper(phase_string)

    # reset the profiling data
    phase_database[phase_string]["temp_data"] = []


def update_phase_database(phase_string, prev2_res, prev1_res, cur_res):
    # do not build model for an idle phase (no trace string)
    if phase_string == "":
        return

    global phase_database

    # first check if we have existing information about the preceding two
    # phases, if not, we do not have a profiling point
    if len(prev1_res) == 0 or len(prev2_res) == 0:
        return

    # check if new or old phase
    if phase_string in phase_database:
        # existing phase
        # only update when we have a batch of batch_size
        if len(phase_database[phase_string]["temp_data"]) < batch_size:
            add_profile(phase_string, prev2_res, prev1_res, cur_res)
        else:
            # time to update the machine learning model
            update_ml_model(phase_string)

    else:
        # create new entry
        val = {"temp_data": [], "models": []}
        phase_database[phase_string] = val
        add_profile(phase_string, prev2_res, prev1_res, cur_res)
        # initialize the models
        add_models(phase_string, cur_res)


def mean_absolute_percentage_error(y_true, y_pred):
    # replace 0 with a small number to avoid div by zero
    y_true = [i if i != 0 else 0.001 for i in y_true]
    y_pred= [i if i != 0 else 0.001 for i in y_pred]

    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100


def detect_anomaly(predicted, cur_resources, cur_phase, phase_status):
    # compare the predicted resource with the current resource
    # each mismatch changes a confidence
    global anom_confidence
    print("Actual:", ["{:.2f}".format(a) for a in cur_resources], "Predicted:", ["{:.2f}".format(a) for a in predicted])
    if cur_phase == "":
        return
    if phase_status == "unseen":
        # use simple heuristic of low CPU utilization for unseen phases
        if cur_resources[0] < 10:
            anom_confidence = anom_confidence + 1
        else:
            anom_confidence = anom_confidence - 1
    else:
        # seen this phase before
        error = mean_absolute_percentage_error(predicted, cur_resources)
        if error > 50:
            anom_confidence = anom_confidence + 1
        else:
            anom_confidence = anom_confidence - 1

    if anom_confidence > 5:
        print("Anomaly Detected.  The following is the stacktrace ")
        print(cur_phase)
        with open('/home/ubuntu/data/phase_db_' + algo, 'wb') as f:
            pickle.dump(phase_database, f)
        exit(0)

def get_current_stage():
    global prev1_resource, prev2_resource

    old_data = stacktrace_helper()  # returns [func_set, [res1 .. resN]]
    time.sleep(interval)
    cur_data = stacktrace_helper()

    # populate the meta-inputs
    prev2_resource = prev1_resource
    prev1_resource = old_data[1]

    # remove the thread information, just use stacktraces for simplicity
    old_trace = set([i.split("***")[0] for i in old_data[0]])
    cur_trace = set([i.split("***")[0] for i in cur_data[0]])

    # detect phase change
    changed = detect_phase_change(old_data[0], cur_data[0])

    # form the key for storing in phase database
    phase_string = form_phase_string(old_trace, cur_trace, changed)

    return phase_string, cur_data[1]


def initialize():
    global phase_database

    # for graceful exit
    signal(SIGINT, handler)

    # load the the phase database if exists
    if os.path.isfile("/home/ubuntu/data/phase_db_" + algo):
        with open('/home/ubuntu/data/phase_db_' + algo, 'rb') as f:
            phase_database = pickle.load(f)
            print("Reloaded phase DB ")


def run_job():
    global prev1_resource, cur_phase
    # get current phase and resource information
    cur_phase, cur_resources = get_current_stage()

    # get prediction
    if cur_phase == "":  # idle phase
        predicted = [0] * num_resources
        phase_status = ""
    else:
        predicted, phase_status = get_prediction(cur_phase)

    # print("Predicted resource usage ", predicted)
    detect_anomaly(predicted, cur_resources, cur_phase, phase_status)

    # update model based on current profile
    update_phase_database(cur_phase, prev2_resource, prev1_resource,
                          cur_resources)

    # one more update
    prev1_resource = cur_resources

if __name__ == '__main__':
    initialize()
    while True:
        try:
            run_job()
        except Exception as e:
            print(e)
            continue