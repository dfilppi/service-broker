# Database utilities

from sqlalchemy import create_engine, Table, Column, MetaData, Integer, String, ForeignKey, Boolean
from sqlalchemy.sql import select, func
import threading


class Database(object):

  def __init__(self, dbpath):
    engine = create_engine('sqlite:///'+dbpath,
             connect_args={'check_same_thread':False})
    self._dbconn = engine.connect()
    metadata = MetaData()

    ##################
    # Table defs
    ##################
    self._server = Table('ServerInfo', metadata,
                 Column('id', Integer, primary_key=True),
                 Column('ip', String),
                 Column('port', Integer),
                 Column('tenant_name', String),
                 Column('user_name', String),
                 Column('password', String))

    self._blueprints = Table('Blueprints', metadata,
                 Column('id', Integer, unique=True, primary_key=True),
                 Column('cloudify_id', String),
                 Column('description', String),
                 Column('bindable', Boolean))

    self._deployments = Table('Deployments', metadata,
                 Column('deployment_id', String, primary_key=True),
                 Column('blueprint_id', Integer),
                 Column('last_operation', String))

    self._inputs = Table('Inputs', metadata,
                 Column('id', Integer, primary_key=True),
                 Column('blueprint', Integer),
                 Column('name', String),
                 Column('type', String),
                 Column('description', String),
                 Column('default', String)
                 )

    self._tags = Table('Tags', metadata,
                 Column('id', Integer, primary_key=True),
                 Column('blueprint', Integer),
                 Column('tag', String))

    self._requires = Table('Requires', metadata,
                 Column('id', Integer, primary_key=True),
                 Column('blueprint', Integer),
                 Column('permission', String))

    metadata.create_all(engine)
    self._lock = threading.Lock()


  ######################################################################
  # Inserts a cloudify server (UNUSED)
  #
  def set_server(self, id, ip, port, tenant_name, user_name, password): 
    with(self._lock):
      ins = server.insert().values(id = id, ip = ip, port = port,
                                 tenant_name = tenant_name,
                                 user_name = user_name, password = password)
      conn.execute(ins)


  ######################################################################
  # List blueprints in database
  #
  # return in catalog syntax for convenience
  #
  def list_blueprints(self):
    with(self._lock):
      results = {}
      services = []
      rows = self._dbconn.execute(select([self._blueprints]))
      for row in rows:
        service = {'name':row['cloudify_id'],
                   'id':row['id'],
                   'description':row['description'],
                   'bindable':row['bindable']
                   }
        services.append(service)
      results['services'] = services
      return results

  
  ######################################################################
  # Get blueprint by id
  #
  def get_blueprint_by_id(self,id):
    with(self._lock):
      row = self._dbconn.execute(select([self._blueprints]).where(
                                  self._blueprints.c.id == id)).fetchone()
      return row
      

  ######################################################################
  # List inputs in database for a blueprint
  #
  def list_inputs(self, blueprint_id):
    with(self._lock):
      rows = self._dbconn.execute(select([self._inputs]).where(
                                  self._inputs.c.blueprint == blueprint_id))
      return rows


  ######################################################################
  # Create a deployment
  #
  def create_deployment(self, deployment_id, blueprint_id):
    with(self._lock):
      ins = self._deployments.insert().values(
                                blueprint_id,
                                deployment_id,
                                "started") 
      self._dbconn.execute(ins)


  ######################################################################
  # Update deployment status
  #
  def update_deployment_status(self, deployment_id, status):
    with(self._lock):
      upd = self._deployments.update().values(status = status).where(
                 self._deployments.c.deployment_id == deployment_id)
      self._dbconn.execute(upd)


  ######################################################################
  # Get deployment status
  #
  def get_deployment_status(self, deployment_id):
    with(self._lock):
      row = self._dbconn.execute(select([self._deployments]).where(
                  self._deployments.c.deployment_id == deployment_id))


  ######################################################################
  # Update db with blueprint info
  #
  def update_blueprints(self, blueprints):
    with(self._lock):
      with self._dbconn.begin():
        for blueprint in blueprints:
          sel = select([func.count(self._blueprints)]).\
                  where(self._blueprints.c.cloudify_id == blueprint['id'])
          #add blueprint if not already there
          if self._dbconn.execute(sel).fetchone()[0] == 0:
            ins = self._blueprints.insert().values(
                    cloudify_id=blueprint['id'],
                    description=blueprint['description'])
            bpid=self._dbconn.execute(ins).inserted_primary_key
            for key,val in blueprint['plan']['inputs'].iteritems():
              inputin = self._inputs.insert().values(
                        blueprint=bpid[0],
                        name=key,
                        type=val['type'] if 'type' in val else None,
                        description=val['description'] if 'description' in val else None,
                        default=val['default'] if 'default' in val and type(val) is not dict else None)
              self._dbconn.execute(inputin)
