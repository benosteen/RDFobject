class ObjectNotFoundException(Exception):
    """Object not found at the ID specified"""
    pass

class VersionNotFoundException(Exception):
    """Version not found"""
    def __init__(self, *p, **kw):
        self.context = (p, kw)
    def __str__(self):
        print " - Version not found: %s" % self.context

class PartNotFoundException(Exception):
    """Part not found"""
    def __init__(self, *p, **kw):
        self.context = (p, kw)
    def __str__(self):
        print " - Part not found: %s" % self.context

class StoreNotFoundException(Exception):
    """Store not found"""
    pass

class ObjectAlreadyExistsException(Exception):
    """Object ID already exists"""
    pass
    
class StoreAlreadyExistsException(Exception):
    """Store ID already exists"""
    pass
    
class NotAPairtreeStoreException(Exception):
    """The directory indicated exists, but doesn't 
    announce itself to be a pairtree store via a
    'pairtree_version0_1' marker file in the root."""
    
class NotAValidStoreName(Exception):
    """Invalid name for a store. Must conform to ^[A-z][A-z0-9]* regex"""
    
class FedoraStoreFailure(Exception):
    """Fedora failed to store or read an item correctly."""
    def __init__(self, resp, content, action):
        self.resp = resp
        self.content = content
        self.action = action
    
    def __repr__(self):
        return "Fedora failed with a status code of %s upon performing action:'%s'\n\nHeaders: %s\nContent: %s" % (self.resp.status, self.action, self.resp, self.content)
