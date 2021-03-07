from flask import Flask
app = Flask(__name__)
DATA_DIR = "/home/ubuntu/data"

@app.route("/worker_data")
def get_worker_data():
    with open(f"{DATA_DIR}/resource_data") as f:
        resource_data = f.read().strip()
    with open(f"{DATA_DIR}/threaddump_data") as f:
        threaddump_data = f.read().strip()

    return {"resource_data": resource_data, "threaddump_data": threaddump_data}
