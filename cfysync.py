# Sync worker for fetching data from cfy manager

from cloudify_rest_client.client import CloudifyClient
from sqlalchemy.sql import select
import threading
import time

SYNC_DELAY = 5

class Syncworker(threading.Thread):

  def __init__(self, db, cfyhost, cfyport, cfytenant, cfyuser, cfypwd):
    threading.Thread.__init__(self)
    self._stop = False
    self._cfyhost = cfyhost
    self._cfyport = cfyport
    self._cfytenant = cfytenant
    self._cfyuser = cfyuser
    self._cfypwd = cfypwd
    self._db = db

  def run(self):
    # connect
    client = CloudifyClient(host=self._cfyhost, port=self._cfyport,
                            trust_all=True, username=self._cfyuser,
                            password=self._cfypwd, tenant=self._cfytenant)
    while(True):
      if self._stop:
        return
      print "updating db"
      self._db.update_blueprints(client.blueprints.list())
      time.sleep(SYNC_DELAY)

  def stop(self):
    self._stop = True

