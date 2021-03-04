import logging

from config import STACK_SIM_THRESHOLD


class Characterizer:
    def __init__(self, database):
        self._database = database
        logging.debug("Characterizer Initialized")

    def get_current_phase(self):
        triplet = self._database.get_triplets()
        prev1_snapshot = triplet[1]
        curr_snapshot = triplet[2]

        phase_changed = self._detect_phase_change(prev1_snapshot, curr_snapshot)
        phase_string = self._form_phase_string(prev1_snapshot, curr_snapshot, phase_changed)

        return phase_string

    def update_phase_database(self, phase_string):
        if phase_string == "":
            return

        triplet = self._database.get_triplets()
        if triplet[0] == None or triplet[1] == None:
            return

        prev2_resources = triplet[0].resource_data
        prev1_resources = triplet[1].resource_data
        curr_resources = triplet[2].resource_data

        profile = []
        num_resources = len(curr_resources)
        for i in range(num_resources):
            profile.append([prev2_resources[i], prev1_resources[i], curr_resources[i]])

        if not self._database.check_phase_exists(phase_string):
            logging.debug("New Phase Detected -> UNSEEN")
            self._database.create_new_phase(phase_string)

        self._database.add_profile_to_phase(profile, phase_string)

    def _detect_phase_change(self, prev_snapshot, curr_snapshot):
        if len(prev_snapshot.stacktrace_data) == 0 and len(curr_snapshot.stacktrace_data) == 0:
            return False
        stack_sim = prev_snapshot.stacktrace_similarity(curr_snapshot)
        logging.debug(f"Stacktrace Sim: {stack_sim}")
        if stack_sim < STACK_SIM_THRESHOLD:
            logging.debug("Phase Change Detected")
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
