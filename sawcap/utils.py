import numpy as np

def MAPE(y_true, y_pred):
    # replace 0 with a small number to avoid div by zero
    y_true = [i if i != 0 else 0.001 for i in y_true]
    y_pred= [i if i != 0 else 0.001 for i in y_pred]

    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    
def SMAPE(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred) # convert to numpy arrays
    return np.mean(np.abs(y_true - y_pred) / (np.abs(y_true) + np.abs(y_pred) + 1e-8)) * 100