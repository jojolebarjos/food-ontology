

import io
import numpy
import sklearn.neural_network
import scipy.sparse
import pickle


# ...
class MLPTrainer:
  def __init__(self, hidden_layer_sizes=(100,), max_iterations=200, verbose=False):
    self._model = sklearn.neural_network.MLPClassifier(
      hidden_layer_sizes=hidden_layer_sizes,
      activation='logistic',
      max_iter=max_iterations,
      solver='lbfgs', # TODO or adam?
      validation_fraction=0.0,
      verbose=verbose
    )
    self._features = []
    self._feature_map = {}
    self._labels = []
    self._label_map = {}
    self._samples = []
  
  # Add sample
  def append(self, features, label):
    
    # Convert features
    features_indices = {}
    for feature, weight in features.items():
      if feature not in self._feature_map:
        self._feature_map[feature] = len(self._features)
        self._features.append(feature)
      feature_index = self._feature_map[feature]
      if feature_index not in features_indices:
        features_indices[feature_index] = 0.0
      features_indices[feature_index] += weight
    
    # Convert label
    if label not in self._label_map:
      self._label_map[label] = len(self._labels)
      self._labels.append(label)
    label_index = self._label_map[label]
    
    # Register sample
    sample = (features_indices, label_index)
    self._samples.append(sample)
  
  # Train and save model
  def train(self, path):
    
    # Build training matrices
    x = scipy.sparse.dok_matrix((len(self._samples), len(self._feature_map)))
    y = numpy.empty([len(self._samples)], dtype=numpy.int32)
    for row in range(len(self._samples)):
      features_indices, label_index = self._samples[row]
      for col, weight in features_indices.items():
        x[row, col] = weight
      y[row] = label_index
    
    # Train model
    try:
      self._model.fit(x, y)
    finally:
    
      # Save model
      with io.open(path, 'wb') as file:
        data = (self._model, self._features, self._labels)
        pickle.dump(data, file)


# ...
class MLPTagger:
  def __init__(self, path):
    with io.open(path, 'rb') as file:
      self._model, self._features, self._labels = pickle.load(file)
    self._feature_map = {feature : index for index, feature in enumerate(self._features)}
  
  def tag(self, features):
    x = scipy.sparse.dok_matrix((1, len(self._features)))
    for feature, weight in features.items():
      if feature in self._feature_map:
        x[0, self._feature_map[feature]] = weight
    y = self._model.predict(x)
    label = self._labels[y[0]]
    return label
