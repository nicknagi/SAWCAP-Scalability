import torch
import numpy as np
from sklearn.preprocessing import MinMaxScaler

def prepare_data_for_training(resource_data, window_size):
	data = np.transpose(resource_data)
	data = torch.Tensor(data)
	scaler = MinMaxScaler(feature_range=(-1, 1))
	data_normalized = scaler.fit_transform(data .reshape(-1, 2))
	input_seq, target_seq = split_data_into_input_and_target(data_normalized, window_size)

	input_seq = torch.Tensor(input_seq)
	target_seq = torch.Tensor(target_seq)
	return input_seq, target_seq, scaler

def split_data_into_input_and_target(data, window_size):
  num_windows = int(np.floor(len(data)/window_size))
  split_data = np.array_split(data[:window_size*num_windows], num_windows)
  input_seq = []
  target_seq = []

  for i in range(len(split_data)):
      # Remove last character for input sequence
    input_seq.append(split_data[i][:-1])
      
      # Remove first character for target sequence
    target_seq.append(split_data[i][1:])
    #print("Input Sequence: \n{}\nTarget Sequence: \n{}\n".format(input_seq[i], target_seq[i]))
  return input_seq, target_seq

def split_data_into_cpu_and_memory(data):
	cpu = []
	memory = []
	for i in range(len(data)):
		cpu.append(data[i][0])
		memory.append(data[i][1])
	return cpu, memory