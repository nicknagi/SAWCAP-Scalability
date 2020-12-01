import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
import os
from sklearn.preprocessing import MinMaxScaler

from data_predictor.models import basic_rnn
from data_predictor import data_utils

# There should only be 1 instance of `DataPredictor` running
class DataPredictor:

	def __init__(self, window_size):
		# all models currently stored in the system
		self.models = {}
		#snapshot size
		self.window_size = window_size

	def handle_data_for_prediction(self, data, model_key):
		if model_key in self.models:
			model = self.models[model_key]
			return self._predict_next_window(model, data)
		# otherwise model is not defined yet, so no prediction can be made
		return None

	def handle_workload_for_retraining(self, data, model_key):
		if model_key in self.models:
			model = self.models[model_key]
			n_epochs = 15
		else:
			model = basic_rnn.basicRNN(model_key, input_size=2, output_size=2, hidden_dim=12, n_layers=1)
			n_epochs = 150

		self._train_on_workload(model, n_epochs, data)
		self.models[model_key] = model

	def _train_on_workload(self, model, n_epochs, data):
		input_seq, target_seq, scaler = data_utils.prepare_data_for_training(data, self.window_size)
		self._train(model, input_seq, target_seq, n_epochs)

	def _train(self, model, input_seq, target_seq, n_epochs, lr = 0.01):
		# Define Loss, Optimizer
		criterion = nn.MSELoss()
		optimizer = torch.optim.Adam(model.parameters(), lr=lr)

		losses = []
		# Training Run
		for epoch in range(1, n_epochs + 1):
			for i, batch in enumerate(input_seq):
				batch = batch.unsqueeze(0)
				optimizer.zero_grad() # Clears existing gradients from previous epoch
				output, hidden = model(batch)
				loss = criterion(output.view(-1), target_seq[i].view(-1))
				losses.append(loss)
				loss.backward() # Does backpropagation and calculates gradients
				optimizer.step() # Updates the weights accordingly
			
			if epoch%50 == 0:
				print('Epoch: {}/{}.............'.format(epoch, n_epochs), end=' ')
				print("Loss: {:.4f}".format(loss.item()))
		return losses

	def _predict_next_window(self, model, data):
		data_with_predictions = data
		for i in range(self.window_size):
			pair = self._predict_next_datapoint(model, data_with_predictions[i:])
			data_with_predictions.append(pair)
		return data_with_predictions[self.window_size:]

	def _predict_next_datapoint(self, model, test_snapshot):
		test_snapshot = torch.Tensor(test_snapshot)
		scaler = MinMaxScaler(feature_range=(-1, 1))
		snapshot_normalized = scaler.fit_transform(test_snapshot .reshape(-1, 2))
		input_seq = []
		input_seq.append(snapshot_normalized)
		input_seq = torch.Tensor(input_seq)
		output, hidden = model(input_seq)
		produced_output = scaler.inverse_transform(np.array(output.detach().numpy()).reshape(-1, 2))
		cpu = self._cap_prediction(produced_output[-1][0])
		memory = self._cap_prediction( produced_output[-1][1])
		return [cpu, memory]

	def _cap_prediction(self, value):
		if value < 0:
			return 0
		return value