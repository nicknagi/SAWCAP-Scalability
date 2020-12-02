import numpy as np
from data_aggregator import data_aggregator
import enum

class CharacterizationState(enum.Enum):
    weak = 0
    initial = 1
    stronger = 2
    strongest = 3

class Workload:

    def __init__(self, initial_snapshot_collection, unique_identifier):
        self._snapshot_collections = [initial_snapshot_collection]
        self.unique_id = unique_identifier
        self.characterization_state = CharacterizationState.initial
        self._len_snapshot_collections_for_aggregation = 1
        self._resource_aggregaion_vector = initial_snapshot_collection.resource_aggregation
    
    def get_latest_snapshot_collection(self):
        return self._snapshot_collections[-1]
    
    def add_new_snapshot_collection(self, snapshot_collection):
        self._snapshot_collections.append(snapshot_collection)

    def calculate_resource_aggregation_vector(self):
        assert(self._len_snapshot_collections_for_aggregation > 0)

        if self._len_snapshot_collections_for_aggregation == len(self._snapshot_collections):
            return self._resource_aggregaion_vector

        resource_data = self._snapshot_collections[0]
        for i, snapshot_collection in enumerate(self._snapshot_collections[1:]):
            resource_data[i] = np.concatenate(resource_data[i], snapshot_collection.resource_data[i])

        self._resource_aggregaion_vector = data_aggregator.generate_resource_aggregation(resource_data)
        self._len_snapshot_collections_for_aggregation = len(self._snapshot_collections)

        return self._resource_aggregaion_vector
