'''
Structure of the database dictionary:
    {
        "triplets": [snapshot_prev2, snapshot_prev1, snapshot_curr],
        "phases": {
            "phase-1" : {
                "temp_data": [ [[cpu_p1, cpu_p2, cpu_c], [mem_p1, mem_p2, mem_c], ..], <-prof1
                [[cpu_p1, cpu_p2, cpu_c], [mem_p1, mem_p2, mem_c], ..], <-prof2
                               .......
                [[cpu_p1, cpu_p2, cpu_c], [mem_p1, mem_p2, mem_c], ..]]<-prof10,
                "models": [model_cpu, model_mem, ...]
            },
            "phase-2" : {
                "temp_data": Same as above,
                "models": model-key
            }
        }
    }
'''

class Database:
    def __init__(self):
        self._database = dict()
        self._database["triplets"] = [None] * 3
        self._database["phases"] = dict()

    def add_new_snapshot(self, snapshot):
        self._database["triplets"][0] = self._database["triplets"][1]
        self._database["triplets"][1] = self._database["triplets"][2]
        self._database["triplets"][2] = snapshot

    def create_new_phase(self, phase_string):
        self._database["phases"][phase_string] = dict()
        self._database["phases"][phase_string]["temp_data"] = list()
        self._database["phases"][phase_string]["models"] = list()

    def add_profile_to_phase(self, profile, phase_string):
        self._database["phases"][phase_string]["temp_data"].append(profile)

    def add_models_to_phase(self, models, phase_string):
        self._database["phases"][phase_string]["models"].append(models)

    def get_triplets(self):
        return self._database["triplets"]

    def get_models_from_phase(self, phase_string):
        return self._database["phases"][phase_string]["models"]

    def get_data_from_phase(self, phase_string):
        return self._database["phases"][phase_string]["temp_data"]

    def check_phase_exists(self, phase_string):
        if phase_string in self._database["phases"]:
            return True
        return False
