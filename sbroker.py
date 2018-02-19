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

VERSION_HEADER = 'X-Broker-API-Version'

app = Flask("cloudify-service-broker")
auto = Autodoc(app)
worker = None
database = None


def parseargs():
    usage = """
        --host <host>          Cloudify server IP or name
        --port <port>          Cloudify server port (default 80)
        --tenant <tenant>      Cloudify tenant (default default_tenant)
        --user <user>          Cloudify user
        --password <password>  Cloudify password
    """
       
    host = None
    port = 80
    tenant = 'default_tenant'
    user = None
    password = None
    while len(sys.argv) > 1:
        arg = sys.argv.pop(1)   
        if arg == '-h':
            print usage
            sys.exit(1)
        elif arg == '--host':
            host = sys.argv.pop(1)
        elif arg == '--port':
            port = sys.argv.pop(1)
        elif arg == '--tenant':
            tenant = sys.argv.pop(1)
        elif arg == '--user':
            user = sys.argv.pop(1)
        elif arg == '--password':
            password = sys.argv.pop(1)
    if not host or not user or not password:
        print 'Missing argument'
        print usage
        sys.exit(1)
    return host,port,tenant,user,password
    
        
def main():
    global worker
    global database
    host,port,tenant,user,password = parseargs()
    database = db.Database('cfy.db')
    worker = Syncworker(database, host, port, tenant, user, password)
    worker.start()
    signal.signal(signal.SIGINT, signal_handler)
    app.run(host='0.0.0.0', port=5000, threaded=True)


# List catalog entries
#
@auto.doc()
@app.route("/v2/catalog", methods=['GET'])
def get_catalog():
    checkapiversion()
    blueprints = database.list_blueprints()

    # just supply a default plan for now
    for service in blueprints['services']:
      plan = { 
             'name':'default',
             'id': service['id'],
             'description': 'default plan',
             'free': True
             }
      service['plan'] = plan
    return jsonify(blueprints),200


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


def checkapiversion():
    if VERSION_HEADER not in request.headers:
       raise MissingHeader('Missing API version header', 400)
    elif request.headers.get(VERSION_HEADER) =='2.13':
       raise MissingHeader('Unsupported API version: use 2.13', 412)

class MissingHeader(Exception):
    status_code = 400
    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@app.errorhandler(MissingHeader)
def handle_missing_header(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

def signal_handler(signal, frame):
    print "stopping sync worker..."
    worker.stop()
    worker.join()
    sys.exit(0)

if __name__ == "__main__":
    main()
