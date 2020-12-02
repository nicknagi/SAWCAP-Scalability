# The entrypoint for the sawcap project - this should be run on the runner i.e the node that monitors the cluster
# get_stacks.sh will be run on each of the workers

class Sawcap:
    
    def __init__(self):
        self.database = Database()
        self.data_collector = DataCollector()

    def run():
        while True:
            # The logic for running everything
            
            pass


if __name__ == "__main__":
    sawcap = Sawcap()
    sawcap.run()