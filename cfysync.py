# Sync worker for fetching data from cfy manager

from cloudify_rest_client.client import CloudifyClient
from sqlalchemy.sql import select
import json
import logging
import threading
import time

SYNC_DELAY = 5
EX_COMPLETE = "terminated"
WF_INSTALL = "install"

##################################################
# Updates the database periodically with blueprint
# info from a Cloudify server.  
##################################################
#
class Syncworker(threading.Thread):


  def __init__(self, db, client, logger):
    threading.Thread.__init__(self)
    self._client = client
    self._stop = False
    self._db = db
    self._logger = logger

  def run(self):

    while(True):

      blueprints = self._client.blueprints.list()

      try:

        self._db.update_blueprints(blueprints)
        if self._stop: 
          self._db.rollback()
          self._db.close()
          return
        
        # Update execution status
        for blueprint in blueprints:
          self._logger.debug( "syncworker -- blueprint: {}".format(blueprint['id']))
          deployments = self._client.deployments.list(["id"], blueprint_id=blueprint['id'])
          if self._stop:
            self._db.rollback()
            self._db.close()
            return
          for deployment in deployments:
            if(self._db.get_deployment_status(deployment['id'])):
              self._logger.debug( "syncworker -- deployment: {}".format(deployment['id']))
              execs = self._client.executions.list(deployment_id = deployment['id'], workflow_id = WF_INSTALL )
              if self._stop:
                self._db.rollback()
                self._db.close()
                return
              for e in execs:
                self._logger.debug( "syncworker -- execution {}".format(e['status']))
                self._db.update_deployment_status(deployment['id'], e['status'])
                if e['status'] == EX_COMPLETE:
                  outputs = self._client.deployments.outputs.get(deployment['id'])
                  self._db.update_deployment_outputs(deployment.id, json.dumps(outputs))
                break

        self._db.commit()

      except(Exception) as e:
        self._logger.error(e.message)
        self._db.rollback()

      for i in range(SYNC_DELAY):
        if self._stop:
          return
        time.sleep(1)

  def stop(self):
    self._stop = True

