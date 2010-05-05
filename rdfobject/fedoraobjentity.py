from constructs import StoredEntity
from stores import FedoraStorageFactory

#from fedoraClient30 import FedoraClient

class FedoraEntityFactory(object):
    def __init__(self, fedora_base = "http://localhost:8080/fedora", root_dsid="RELS-EXT", manifest_dsid="RELS-INT", username="", password="", uri_base="info:fedora/"):
        if not(uri_base.endswith('/') or uri_base.endswith('#')):
            uri_base = "%s/" % uri_base
        self.uri_base = uri_base
        factory_f = FedoraStorageFactory()
        self.s = factory_f.get_store(FedoraClient(server=fedora_base, username=username, password=password), root_dsid, manifest_dsid, uri_base)

    def get_id(self, id=None):
        uri = "%s%s" % (self.uri_base, id)
        s = StoredEntity(uri)
        s.init(id, self.s)
        return s

    def get(self, uri):
        if uri.startswith(self.uri_base):
            id = uri[len(self.uri_base):]
        s = StoredEntity(uri)
        s.init(id, self.s)
        return s
        
