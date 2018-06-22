from binder import Binder
import hvac
import json

class VaultBinder(Binder):

  def __init__(self, log):
    self._log = log

  """
  Vault binder for Cloudify
  """

  def connect(self, creds):
    """
    vault credential string format: <token>@<url>
    """
    url, token = creds.split('@')
    self._client = hvac.Client(url=url, token=token)


  def configure(self, config, outputs):
    """
     config is a string which parses to meaningful key/value pairs (e.g. host)
     outputs is a python dict of key value pairs
    """
    if outputs == None :
      self._config = eval(config)
      return

    i = 0
    end = -1
    self._config = ""
    while i < len(config) and i > -1:
      lend = end
      val, beg, end = self._eval_config( config, outputs, i)
      if beg < 0:
        self._log.debug("CONFIG={}".format(config))
        lastp = config.rfind('}}')
        if(lastp != -1):
          self._config += config[lastp+2:]
        break
      if beg > i:
        self._config += config[i: beg]
      self._config += val
      i = end + 1
      if i > len(config):
        break
    if self._config == "":
      self._config = config
    self._config = eval(self._config) # must eval to dict
    self._log.debug("cfg = {}".format(self._config))
    
  def get_creds(self, service):
    """
    service = a path in vault to read credentials from
    """
    creds = self._client.read(service)['data']
    creds.update(self._config)
    return creds

  def _eval_config(self, config, outputs, start ):
    """
    returns results from parse, and begining and end of location
    """
    beg = config.find("{{", start)
    if beg<0 or beg >len(config)-1:
      return None, -1, -1
    end = config.find("}}", beg+1)
    ss =  config[beg+2: end].strip()
    evals = "outputs[\"outputs\"]"+ss
    return eval(evals), beg, end
