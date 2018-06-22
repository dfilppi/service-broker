from abc import ABCMeta, abstractmethod

#
# Base class for binder impls
#
class Binder():
  __metaclass__ = ABCMeta
  
  @abstractmethod
  def connect(self, creds):
    pass

  @abstractmethod
  def configure(self, config, outputs):
    pass

  @abstractmethod
  def get_creds(self, service):
    pass
