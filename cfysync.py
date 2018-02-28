# Sync worker for fetching data from cfy manager

from cloudify_rest_client.client import CloudifyClient
from sqlalchemy.sql import select
import threading
import time

SYNC_DELAY = 5

##################################################
# Updates the database periodically with blueprint
# info from a Cloudify server.  
##################################################
#
class Syncworker(threading.Thread):

  def __init__(self, client):
    threading.Thread.__init__(self)
    self._client = client
    self._stop = False
    self._db = db

  def run(self):
    # connect
    while(True):
      if self._stop:
        return
      self._db.update_blueprints(self._client.blueprints.list())
      time.sleep(SYNC_DELAY)

  def stop(self):
    self._stop = True

