import numpy as np

# There should only be 1 instance of `DataPredictor` running
# We can move some of the ML and state machine logic in here later
class DataPredictor:

	# array to store past feature vectors
	# feature_vectors is an N x 2 array
	feature_vectors = np.array([])

	# threshold for matching 
	threshold = 0.9	

	def __init__(self):
		pass

	def updateFeatureVectors(feature_vectors):
		self.feature_vectors = feature_vectors

	# calculate the euclidean distance
	# curr_vector is a 1 x 2 vector
	# return an N x 1 vector of distances
	def euclideanDistance(self, curr_vector):
		diff = self.feature_vectors - curr_vector
		return np.linalg.norm(diff, axis=1)

	# curr_vector is a 1 x 2 vector
	# return a metric in the range (0, 1)
	def clusteringDistance(self, curr_vector):
		distance = euclideanDistance(curr_vector)
		t = feature_vectors.shape[0]

		# the heuristic we are using for clustering is sum(1 / [1 + distance(xi, yi)])/t
		heuristic = 1 / (1 + distances)
		return np.sum(heuristic) / t

	# a workload is recognized if the minimum of all weights is less than the threshold
	def recognizeWorkloads(self, curr_vector):
		return clusteringDistance(curr_vector) < 0.9

