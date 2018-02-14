from flask import Flask, request, jsonify
from flask_autodoc.autodoc import Autodoc
from cloudify_rest_client.client import CloudifyClient
from templates import catalog_t
from cfysync import Syncworker
import signal
import sys
import db

# Cloudify service broker implementation
#
# Limitations:
#   - no TLS
#   - no real authentication (faked basic auth)
#   - headers ignores (e.g. X-Broker-Api-Version)


app = Flask("cloudify-service-broker")
auto = Autodoc(app)
worker = None

def main():
    global worker
    worker = Syncworker(db.Database('cfy.db'), "10.239.0.192",80, "default_tenant", "admin", "admin")
    worker.start()
    signal.signal(signal.SIGINT, signal_handler)
    app.run(host='0.0.0.0', port=5000, threaded=True)


# List catalog entries
#
@auto.doc()
@app.route("/v2/catalog", methods=['GET'])
def get_catalog():
    pass


# Provision an service
#
@auto.doc()
@app.route("/v2/service_instances/<service_id>", methods=['PUT'])
def provision(service_id):
    pass


# Deprovision
#
@auto.doc()
@app.route("/v2/service_instances/<instance_id>", methods=['DELETE'])
def deprovision(instance_id):
    pass


# Update an entry
#
@auto.doc()
@app.route("/v2/service_instances/<service_id>", methods=['PATCH'])
def update(service_id):
    pass


# Bind
#
@auto.doc()
@app.route("/v2/service_instances/<instance_id>/service_bindings/<binding_id>", methods=['PUT'])
def bind(service_id, binding_id):
    pass


# Unbind
#
@auto.doc()
@app.route("/v2/service_instances/<instance_id>/service_bindings/<binding_id>", methods=['DELETE'])
def unbind(service_id, binding_id):
    pass

def signal_handler(signal, frame):
    worker.stop()
    worker.join()
    sys.exit(0)

if __name__ == "__main__":
    main()
