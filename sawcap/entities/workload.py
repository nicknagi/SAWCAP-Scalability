class Workload:

    def __init__(self, initial_snapshot_collection, unique_identifier):
        self._snapshot_collections = [initial_snapshot_collection]
        self.unique_id = unique_identifier
    
    def get_latest_snapshot(self):
        return self._snapshot_collections[-1]
    
    def add_new_snapshot(self, snapshot_collection):
        self._snapshot_collections.append(snapshot_collection)