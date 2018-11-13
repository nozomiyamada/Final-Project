import numpy as np
feature_matrix = np.array([1, 0, 100])
parameter_matrix = np.array( [[ -2, 2, -1], [-1, -0.2, 0.4], [0.0004, 0.005, -0.00001]])
output = np.matmul(feature_matrix,parameter_matrix)
print('Probabilities = {}'.format(np.exp(output) / np.exp(output).sum()))
