from binder import Binder
import hvac
import json
import sys

class VaultBinder(Binder):

  def __init__(self, log):
    self._log = log
    self._client = None

  """
  Vault binder for Cloudify
  """

  def connect(self, creds):
    """
    vault credential string format: <token>@<url>
    """
    token, url = creds.split('@')
    self._client = hvac.Client(url=url, token=token)
    if not self._client:
      self._log.error("failed to connect to Vault instance:{}".format(creds))
      sys.exit(1)


  def configure(self, config, outputs):
    """
     config is a path in vault which contains config key value pairs json encoded
     outputs is a python dict of key value pairs
    """
    self._outputs = outputs
  
    if not config:
      raise Exception("no config supplied")

    self._log.debug(" configure config = {}".format(config))
    confstr = self._client.read(config)['data']['config']

    if not confstr:
      raise Exception("no config supplied")

    if outputs == None :
      self._config = eval(confstr)
      return

    # Loop through all output substitutions in config string
    # Result must be a dict, which will be passed to vault to
    # configure the secret engine
    i = 0
    end = -1
    self._config = ""
    while i < len(confstr) and i > -1:
      lend = end
      val, beg, end = self._eval_config( confstr, outputs, i)
      if beg < 0:
        lastp = confstr.rfind('}}')
        if(lastp != -1):
          self._config += confstr[lastp+2:]
        break
      if beg > i:
        self._config += confstr[i: beg]
      self._config += val
      i = end + 1
      if i > len(confstr):
        break
    if self._config == "":
      self._config = config
    self._config = eval(self._config) # must eval to dict
 
    # Write path to vault (if needed)
    res = self._client.read(self._config['__path__'])
    path = self._config['__path__']
    if not res:
      config = self._config.copy()
      del(config['__path__'])
      self._log.debug("writing path {} = {}".format(path,config))
      self._client.write( path, **config)
      self._log.debug("wrote path {} = {}".format(path,config))
    else:
      self._log.debug("path '{}' found, not writing".format(path))

  def get_creds(self):
    """
    service = a path in vault to read credentials from
    """
    creds = self._client.read(self._config['__credpath__'])['data']
    self._log.debug("get_creds from {} return: {}".format(self._config['__path__'], creds))
    if self._outputs:
      for k,v in self._outputs.iteritems():
        if isinstance(v,dict):
          self._log.debug("updating creds with output: {}".format(v))
          creds.update(v)
    return creds

  def _eval_config(self, config, outputs, start ):
    """
    returns results from parse, and begining and end of location
    searches for expression bounded by {{}}, and substitutes the Cloudify
    output of the same name
    """
    beg = config.find("{{", start)
    if beg<0 or beg >len(config)-1:
      return None, -1, -1
    end = config.find("}}", beg+1)
    ss =  config[beg+2: end].strip()
    evals = "outputs[\"outputs\"]"+ss
    return eval(evals), beg, end
