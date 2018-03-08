from flask import Flask, request, jsonify, json
from flask_autodoc.autodoc import Autodoc
from cloudify_rest_client.client import CloudifyClient
from cfysync import Syncworker
import uuid
import signal
import sys
import db

# Cloudify service broker implementation
#
# Limitations:
#   - no TLS
#   - no real authentication (faked basic auth)
#   - headers ignores (e.g. X-Broker-Api-Version)
#   - header X-Broker-API-Origin ignored

VERSION_HEADER = 'X-Broker-API-Version'

app = Flask("cloudify-service-broker")
auto = Autodoc(app)
worker = None
database = None
client = None


########################################
# Parse CLI args
########################################
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
    global client
    host,port,tenant,user,password = parseargs()
    database = db.Database('cfy.db')
    client = CloudifyClient(host=host, port=port,
                            trust_all=True, username=user,
                            password=password, tenant=tenant)
    worker = Syncworker(database, client)
    worker.start()
    signal.signal(signal.SIGINT, signal_handler)
    app.run(host='0.0.0.0', port=5000, threaded=True)


########################################
########################################
# REST API
########################################
########################################

########################################
# List catalog entries
########################################
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
      service['plans'] = [] if 'plans' not in service else service['plans']
      service['plans'].append(plan)
    return jsonify(blueprints), 200


########################################
# Provision a service
#
########################################
#
@auto.doc()
@app.route("/v2/service_instances/<instance_id>", methods=['PUT'])
def provision(instance_id):
    checkapiversion()

    # Handle async query arg   ####################
    asyncflag = False
    try:
      asyncflag = bool(request.args.get("accepts_incomplete"))
    except: 
      pass
    if not asyncflag:
      return '{"error":"AsyncRequired","description":"This service plan requires client support for asynchronous service operations."}', 422

    # parse body  ####################
    body = json.loads(request.data)    
    service_id = body['service_id']
    blueprint_id = database.get_blueprint_by_id(service_id)
    plan_id = body['plan_id']
    # ignore context for now
    # ignore org_guid
    # ignore space_guid
    inputs = body['parameters']

    deployment = client.deployments.create(blueprint_id, instance_id, inputs)
    if not deployment:
      return "Deployment creation failed", 500
    execution = client.executions.start(instance_id, "install")
    if not ( execution.status == Execution.STARTED or
             execution.status == Execution.PENDING ):
     return "Install execution failed", 500

    # Update deployment state
    database.create_deployment(instance_id, blueprint_id)
    return "",202

    
########################################
# Polling last operation
#
# WIP
#
########################################
#
@auto.doc()
@app.route("/v2/service_instances/<instance_id>/last_operation", methods=['GET'])
def poll(instance_id):
    checkapiversion()

    service_id = request.args.get("service_id")
    plan_id = request.args.get("plan_id")
    operation = request.args.get("operation")

    status = db.get_deployment_status(instance_id)
    if not status:
      return "Unknown instance", 500
    elif status == "started":
      # query server for current status
      pass
    elif status == "running":
      # query server for current status 
      pass
    elif status == "stopped":
      # return status
      pass
    elif status == "error":
      # return status
      pass
    else:
      return "Unknown status:"+status, 500


###########################################################
# Deprovision
#
@auto.doc()
@app.route("/v2/service_instances/<instance_id>", methods=['DELETE'])
def deprovision(instance_id):
    checkapiversion()


###########################################################
# Update an entry
#
@auto.doc()
@app.route("/v2/service_instances/<service_id>", methods=['PATCH'])
def update(service_id):
    checkapiversion()


###########################################################
# Bind
#
@auto.doc()
@app.route("/v2/service_instances/<instance_id>/service_bindings/<binding_id>", methods=['PUT'])
def bind(service_id, binding_id):
    checkapiversion()


###########################################################
# Unbind
#
@auto.doc()
@app.route("/v2/service_instances/<instance_id>/service_bindings/<binding_id>", methods=['DELETE'])
def unbind(service_id, binding_id):
    checkapiversion()


########################################
########################################
# Utility functions
########################################
########################################

def checkapiversion():
    if VERSION_HEADER not in request.headers:
       raise MissingHeader('Missing API version header', 400)
    elif request.headers.get(VERSION_HEADER) !='2.13':
       raise MissingHeader('Unsupported API version: {} use 2.13'.format(request.headers.get(VERSION_HEADER)), 412)

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
