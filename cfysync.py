# Sync worker for fetching data from cfy manager

from cloudify_rest_client.client import CloudifyClient
from sqlalchemy.sql import select
import db
import threading
import time


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
      self._db.update_blueprints(client.blueprints.list())
      return 


  def stop(self):
    self._flag = True

t = Syncworker(db.Database('cfy.db'), "10.239.0.192",80, "default_tenant", "admin", "admin")

t.start()

t.stop()

t.join()
