from collections import defaultdict
import uuid

# Class assumes workload class exists

'''
Structure of the database dictionary:
    {
        "characterization_queue": [workload3],
        "classes": {
            "uuid4-1" : {
                "workloads": [workload1, workload4],
                "model": model-key -- predictor maintains internal data_structure that stores the models
            },
            "uuid4-2" : {
                "workloads": [workload2],
                "model": model-key
            }
        }
    }
'''
class Database:
    def __init__(self):
        self._database = dict()
        self._database["characterization_queue"] = list()
        self._database["id_to_workload"] = dict()
        self._database["workload_classes"] = dict()

    def add_new_workload(self, workload):
        self._database["characterization_queue"].append(workload)
        self._database["id_to_workload"][workload.unique_id] = workload
    
    def create_new_workload_class(self):
        new_class_id = str(uuid.uuid4())
        self._database["workload_classes"][new_class_id] = dict()
        self._database["workload_classes"][new_class_id]["workloads"] = list()

        return new_class_id
    
    def add_workload_to_class(self, workload, class_id):
        self._database["workload_classes"][class_id]["workloads"].append(workload)
    
    def add_model_to_workload_class(self, class_id, model_id):
        self._database["workload_classes"][class_id]["model"] = model_id

    def get_uncharacterized_workloads(self):
        return self._database["characterization_queue"]

    def get_workload_from_id(self, unique_id):
        return self._database["id_to_workload"][unique_id]
    
    def get_model_id_from_class(self, workload_class_id):
        return self._database["workload_classes"][workload_class_id]["model"]
    
    def get_all_workload_classes(self):
        return list(self._database["workload_classes"].keys())

    def get_workloads_from__workload_class(self, workload_class_id):
        return self._database["workload_classes"][workload_class_id]["workloads"]
