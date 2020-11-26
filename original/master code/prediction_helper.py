import numpy as np

# feature_vectors is an N x 2 array, curr_vector is a 1 x 2 vector
def euclideanDistance(feature_vectors, curr_vector):
  # get an N x 1 vector of distances
  diff = feature_vectors - curr_vector
  return np.linalg.norm(diff, axis=1)

# distances is the eucliden distances between feature vectors
def clusteringDistance(distances):
  # the heuristic we are using for clustering is sum(1 / [1 + distance(xi, yi)])
  heuristic = 1 / (1 + distances)
  return np.sum(heuristic)


# test runner for above functions
if __name__ == '__main__':
    test_data = np.random.rand(10,2)
    input_vector =  np.random.rand(1,2)

    eucl_dist = euclideanDistance(test_data, input_vector)
    dist = clusteringDistance(eucl_dist)
    print(dist)
