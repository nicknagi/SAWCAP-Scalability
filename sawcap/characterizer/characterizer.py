import logging
from config import LOG_LEVEL, STACK_SIM_THRESHOLD

class Characterizer:
    def __init__(self, database):
        self._database = database
        logging.debug("Characterizer Initialized")

    def run(self):
        triplet = self._database.get_triplets()

        self._check_phase_and_update_database(triplet)

    def _check_phase_and_update_database(self, triplet):
        prev2_snapshot = triplet[0]
        prev1_snapshot = triplet[1]
        curr_snapshot = triplet[2]
        
        phase_changed = self._detect_phase_change(prev1_snapshot, curr_snapshot)
        phase_string = self._form_phase_string(prev1_snapshot, curr_snapshot, phase_changed)

        if prev2_snapshot == None or prev1_snapshot == None:
            return

        self._update_phase_database(phase_string, prev2_snapshot.resource_data,
                                    prev1_snapshot.resource_data, curr_snapshot.resource_data)

    def _detect_phase_change(self, prev_snapshot, curr_snapshot):
        stack_sim = prev_snapshot.stacktrace_similarity(curr_snapshot)
        logging.debug(f"Stacktrace Sim: {stack_sim}")
        if stack_sim < STACK_SIM_THRESHOLD:
            logging.info("Phase Change Detected")
            return True
        return False

    def _form_phase_string(self, prev_snapshot, curr_snapshot, phase_changed):
        common_functions = prev_snapshot.stacktrace_data.intersection(curr_snapshot.stacktrace_data)
        if phase_changed:
            common_functions = curr_snapshot.stacktrace_data
        phase_string = ""
        for function in common_functions:
            phase_string += str(function) + "->"
        return phase_string

    # Model class needs to check the database for all phases that need training and then flush temp_data and create/update models
    def _update_phase_database(self, phase_string, prev2_resources, prev1_resources, curr_resources):
        if phase_string == "":
            return

        profile = []
        num_resources = len(curr_resources)
        for i in range(num_resources):
            profile.append([prev2_resources[i], prev1_resources[i], curr_resources[i]])

        if not self._database.check_phase_exists(phase_string):
            logging.info("New Phase Detected -> UNSEEN")
            self._database.create_new_phase(phase_string)
        
        self._database.add_profile_to_phase(profile, phase_string)
