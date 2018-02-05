from flask import Flask, request, jsonify
from flask_autodoc.autodoc import Autodoc
from cloudify_rest_client.client import CloudifyClient

# Cloudify service broker implementation
#
# Limitations:
#   - no TLS
#   - no real authentication (faked basic auth)


app = Flask("cloudify-service-broker")
auto = Autodoc(app)

def main():
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


if __name__ == "__main__":
    #app.run(host='0.0.0.0', port=5000, threaded=True)
    client = CloudifyClient(host="10.239.0.192", port=8100, trust_all=True, username="admin",
                            password="admin", tenant="default_tenant")
    for b in client.blueprints.list():  
        print b.id

