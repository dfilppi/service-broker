from flask import Flask, request, jsonify, json
from flask_autodoc.autodoc import Autodoc
from cloudify_rest_client.client import CloudifyClient, exceptions
from cloudify_rest_client.executions import Execution
from cfysync import Syncworker
import logging
import uuid
import signal
import sys
import time
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

logging.basicConfig(filename="sbroker.log", format="%(asctime)s %(levelname)-7s %(module)s %(funcName)8.8s - %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(10)


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
    worker = Syncworker(database, client, logger)
    worker.start()
    signal.signal(signal.SIGINT, signal_handler)
    app.run(host='0.0.0.0', port=5000, threaded=True)


########################################
########################################
# OPEN SERVICE BROKER REST API
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

    logger.debug( "PROVISIONING")

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
    blueprint_id = database.get_blueprint_by_id(service_id)[1]
    plan_id = body['plan_id']
    # ignore context for now
    # ignore org_guid
    # ignore space_guid

    # Check for existence
    err = False
    try:
      deployment = client.deployments.get( instance_id)
    except exceptions.CloudifyClientError as e:
      err = True

    if not err:
      # Already exists
      logger.debug("deployment exists")
      return jsonify({"dashboard_url":"http://none.com"}), 200

    inputs = body['parameters'] if 'parameters' in body else None

    deployment = client.deployments.create(blueprint_id, instance_id, inputs)

    if not deployment:
      return "Deployment creation failed", 500

    # Launch install execution
    time.sleep(2)   # takes longer than this for deployment creation
    i = 0
    execution = None
    for i in range(30):
      try:
        execution = client.executions.start(instance_id, "install")
        break
      except (exceptions.DeploymentEnvironmentCreationPendingError,
              exceptions.DeploymentEnvironmentCreationInProgressError):
        logging.debug("waiting for env")
        time.sleep(2)    

    if i == 29:
      return "Install execution timed out", 500

    if not ( execution.status == Execution.STARTED or
             execution.status == Execution.PENDING ):
      return "Install execution failed", 500

    # Update deployment state
    database.create_deployment(instance_id, blueprint_id)

    return "{}",202

    
########################################
# Polling last operation
#
# Asynchronous polling for operation status
#
########################################
#
@auto.doc()
@app.route("/v2/service_instances/<instance_id>/last_operation", methods=['GET'])
def poll(instance_id):
    checkapiversion()

    logging.debug("POLLING")

    service_id = request.args.get("service_id")
    plan_id = request.args.get("plan_id")
    operation = request.args.get("operation")

    status = database.get_deployment_status(instance_id)
    if not status:
      logging.error("NO STATUS")
      return jsonify({"description":"Unknown instance"}), 500
    elif status == "started":
      return jsonify({"state":"in progress","description":"Service instantiation in progress"})
    elif status == "cancelled":
      return jsonify({"state":"error","description":"Service cancelled"})
    elif status == "error":
      return jsonify({"state":"error","description":"Service instantiation failed"})
    elif status == "terminated":
      return jsonify({"state":"succeeded","description":"Service instantiation complete"})
    else:
      logging.error("ELSE = {}".format(status))
      return jsonify({"description":"Unknown status = {}".format(status)}), 500


###########################################################
# Deprovision
#
@auto.doc()
@app.route("/v2/service_instances/<instance_id>", methods=['DELETE'])
def deprovision(instance_id):
    checkapiversion()
    return "", 200


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
# CLI SUPPORT REST API
########################################


########################################
########################################
# Utility functions
########################################
########################################

def checkapiversion():
    if VERSION_HEADER not in request.headers:
       raise MissingHeader('Missing API version header', 400)
    elif request.headers.get(VERSION_HEADER) !='2.13':
       raise MissingHeader(jsonify({"description":'Unsupported API version: {} use 2.13'.format(request.headers.get(VERSION_HEADER))}), 412)

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
