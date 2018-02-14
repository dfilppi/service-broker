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
                 Column('id', Integer, primary_key=True),
                 Column('cloudify_id', String),
                 Column('description', String),
                 Column('bindable', Boolean))

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
  #
  #
  def set_server(self, id, ip, port, tenant_name, user_name, password): 
    with(self._lock):
      ins = server.insert().values(id = id, ip = ip, port = port,
                                 tenant_name = tenant_name,
                                 user_name = user_name, password = password)
      conn.execute(ins)


  ######################################################################
  # Update db with blueprint info
  #
  def update_blueprints(self, blueprints):
    with(self._lock):
      for blueprint in blueprints:
        sel = select([func.count(self._blueprints)]).where(self._blueprints.c.cloudify_id == blueprint['id'])
        #add blueprint if not already there
        if self._dbconn.execute(sel).fetchone()[0] == 0:
          ins = self._blueprints.insert().values(
                  cloudify_id=blueprint['id'],
                  description=blueprint['description']
                  )
          bpid=self._dbconn.execute(ins).inserted_primary_key
          for key,val in blueprint['plan']['inputs'].iteritems():
            inputin = self._inputs.insert().values(
                      blueprint=bpid,
                      name=key,
                      type=val['type'] if 'type' in val else None,
                      description=val['description'] if val['description'] else None,
                      default=val['default'] if val['default'] else None)
            self._dbconn.execute(inputin)
        break
