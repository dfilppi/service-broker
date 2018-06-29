from abc import ABCMeta, abstractmethod

#
# Base class for binder impls
#
class Binder():
  __metaclass__ = ABCMeta
  
  @abstractmethod
  def connect(self, creds):
    """Connect to a secret engine.

       Implemention logic is optional if lazy approach is preferred.
       Implementions should store connection information 
       No return value
    """ 
    pass

  @abstractmethod
  def configure(self, config, outputs):
    """Configure a binding

       If required by the engine, configure the target service.
       "config" is the secret engine specific configuration for the service.
       "outputs" is a dictionary of values from the Cloudify deployment
       that can be used to enrich the configuration.
       No return value
    """
    pass

  @abstractmethod
  def get_creds(self):
    """Retrieve credentials from the engine

       Returns a dictionary of credentials for return to K8S.
    """
    pass
