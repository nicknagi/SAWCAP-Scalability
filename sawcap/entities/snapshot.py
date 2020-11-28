# Class for representing a snapshot entity

class Snapshot:
    def __init__(self, window_size, resource_data, stacktrace_data):
        self.window_size = window_size
        self.resource_data = resource_data
        self.stacktrace_data = stacktrace_data