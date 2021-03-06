# Database utilities

from sqlalchemy import create_engine, Table, Column, MetaData, Integer, String, ForeignKey, Boolean
from sqlalchemy.sql import select, func
from sqlalchemy.orm import sessionmaker
import threading


class Database(object):

  def __init__(self, dbpath):
    self._lock = threading.Lock()

    with(self._lock):
      engine = create_engine('sqlite:///'+dbpath,
               connect_args={'check_same_thread':False})
      self._session = sessionmaker(bind=engine, autocommit = False)() 
      metadata = MetaData()
  
      self._blueprints = Table('Blueprints', metadata,
                   Column('id', Integer, unique=True, primary_key=True),
                   Column('cloudify_id', String),
                   Column('description', String),
                   Column('binder', String),
                   Column('binder_config', String)
                   )
  
      self._deployments = Table('Deployments', metadata,
                   Column('deployment_id', String, primary_key=True),
                   Column('blueprint_id', Integer),
                   Column('outputs', String),
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
  # return in catalog syntax for convenience.  If canonical is true, ensure
  # proper service catalog naming [-a-zA-Z0-9]
  #
  def list_blueprints(self, canonical=False):
    with(self._lock):
      results = {}
      services = []
      rows = self._session.execute(select([self._blueprints]))
      for row in rows:
        name = row['cloudify_id'].replace('_','-') if canonical else row['cloudify_id']
        service = {'name':name,
                   'id':str(row['id']),
                   'description':row['description'],
                   'binder': row['binder']
                   }
        if not service['description'] or len(service['description']) ==0:
          service['description'] = 'undescribed'
        services.append(service)
      results['services'] = services
      return results

  
  ######################################################################
  # Get blueprint by id
  #
  def get_blueprint_by_id(self,id):
    with(self._lock):
      row = self._session.execute(select([self._blueprints]).where(
                                  self._blueprints.c.id == id)).fetchone()
      return row
      
  ######################################################################
  # Get blueprint by instance/deployment id
  #
  def get_blueprint_by_deployment_id(self,instance_id):
    with(self._lock):
      row = self._session.execute(select([self._deployments]).where(
                                  self._deployments.c.deployment_id == instance_id)).fetchone()
      return self._session.execute(select([self._blueprints]).where(
                                  self._blueprints.c.id == row['blueprint_id'])).fetchone()
      

  ######################################################################
  # List inputs in database for a blueprint
  #
  def list_inputs(self, blueprint_id):
    with(self._lock):
      rows = self._session.execute(select([self._inputs]).where(
                                  self._inputs.c.blueprint == blueprint_id))
      return rows


  ######################################################################
  # Create a deployment
  #
  def create_deployment(self, deployment_id, blueprint_id):
    with(self._lock):
      ins = self._deployments.insert().values(
                                blueprint_id = blueprint_id,
                                deployment_id = deployment_id,
                                last_operation = "started") 
      self._session.execute(ins)


  ######################################################################
  # Update deployment status
  #
  def update_deployment_status(self, deployment_id, status):
    with(self._lock):
      upd = self._deployments.update().values(last_operation = status).where(
                 self._deployments.c.deployment_id == deployment_id)
      self._session.execute(upd)

  ######################################################################
  # Update deployment outputs
  #
  def update_deployment_outputs(self, deployment_id, outputs):
    with(self._lock):
      upd = self._deployments.update().values(outputs = outputs).where(
                 self._deployments.c.deployment_id == deployment_id)
      self._session.execute(upd)

  ######################################################################
  # Get deployment status
  #
  def get_deployment_status(self, deployment_id):
    with(self._lock):
      row = self._session.execute(select([self._deployments]).where(
                  self._deployments.c.deployment_id == deployment_id)).fetchone()
      if not row: return None
      return row['last_operation']

  ######################################################################
  # Get deployment
  #
  def get_deployment(self, deployment_id):
    with(self._lock):
      row = self._session.execute(select([self._deployments]).where(
                  self._deployments.c.deployment_id == deployment_id)).fetchone()
      if not row: return None
      return row

  ######################################################################
  # Update db with blueprint info
  #
  def update_blueprints(self, blueprints):
    with(self._lock):
      for blueprint in blueprints:
        sel = select([func.count(self._blueprints)]).\
                where(self._blueprints.c.cloudify_id == blueprint['id'])
        #add blueprint if not already there
        if self._session.execute(sel).fetchone()[0] == 0:
          ins = self._blueprints.insert().values(
                  cloudify_id=blueprint['id'],
                  description=blueprint['description'])
          bpid=self._session.execute(ins).inserted_primary_key
          for key,val in blueprint['plan']['inputs'].iteritems():
            inputin = self._inputs.insert().values(
                      blueprint=bpid[0],
                      name=key,
                      type=val['type'] if 'type' in val else None,
                      description=val['description'] if 'description' in val else None,
                      default=val['default'] if 'default' in val and type(val) is not dict else None)
            self._session.execute(inputin)

  ######################################################################
  # Check binding
  #
  def binding_exists(self, binding_id):
    with(self._lock):
      row = self._session.execute(select([self._bindings]).where(
                  self._bindings.c.id == binding_id)).fetchone()
      return row != None

  ######################################################################
  # Add binding.  Returns success boolean
  #
  def add_binding(self, binding_id, instance_id, plan_id):
    try:
      with(self._lock):
        ins = self._bindins.insert().values( 
                                 id = binding_id,
                                 instance = instance_id,
                                 plan = plan_id)
        self._session.execute(ins)
    except:
      return False
    return True

  ###################################################################
  # begin/commit/rollback

  def commit(self): self._session.commit()

  def rollback(self): self._session.rollback()
 
  def close(self): return self._session.close

