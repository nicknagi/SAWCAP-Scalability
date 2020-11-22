'''
Goal of this file is to see the long-term time-series prediction capabilitites of a Lasso model!
'''

from sklearn import linear_model
import os
import pickle
import numpy as np

def mean_absolute_percentage_error(y_true, y_pred):
    # replace 0 with a small number to avoid div by zero
    y_true = [i if i != 0 else 0.001 for i in y_true]
    y_pred= [i if i != 0 else 0.001 for i in y_pred]

    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

my_ds = []
algo = "lasso"
phase_database = {}
with open("phase_db_lasso", 'rb') as f:
    phase_database = pickle.load(f)
    print("Reloaded phase DB ")

counter = 0
for k,v in phase_database.items():
    if len(v["all_data"]) >= 5:
        my_ds.append(dict())
        my_ds[counter]["model"] = v["models"]
        my_ds[counter]["data"] = v["all_data"]
        counter += 1

from pprint import pprint
pprint(my_ds)

for phase in my_ds:
    input_data = []
    expected_data = []
    for entry in phase["data"]:
        input_data.append([entry[1][1], entry[1][0]])
        expected_data.append(entry[1][2])
    # MEM
    print(f"Length of dataset: {len(phase['data'])}")
    predictions = phase["model"][1].predict(input_data)
    print(f"SMAPE Error: {mean_absolute_percentage_error(expected_data, predictions)}")