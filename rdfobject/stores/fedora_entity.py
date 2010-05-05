from rdflib import Namespace

from rdfobject import RDFobject

from storage_exceptions import ObjectNotFoundException, ObjectAlreadyExistsException, FedoraStoreFailure

from rdfobject.constructs import Manifest, ItemAlreadyExistsException, ItemDoesntExistException

class FedoraStorageFactory(object):
    def get_store(self, fedoraclient, root_dsid, manifest_dsid, uri_base):
        return FedoraStorageClient(fedoraclient, root_dsid="RELS-EXT", manifest_dsid="RELS-INT", uri_base="info:fedora/")
        

class FedoraStorageClient(object):
    def __init__(self, fedoraclient, root_dsid, manifest_dsid, uri_base):
        self.f = fedoraclient
        self.root_dsid = root_dsid
        self.manifest_dsid = manifest_dsid
        self.uri_base = Namespace(uri_base)

    def _id_to_uri(self, id):
        return self.uri_base[id]

    def exists(self, id):
        return self.f.ri.doesPIDExist(self._id_to_uri(id))

    def _create(self, id):
        root = RDFobject()
        root.set_uri(self.uri_base[id])
        now = datetime.now()
        root.add_triple(u'dcterms:created', now)
        self._store_rdfobject(id, self.root_dsid, root)
        return FedoraStoredObject(id, self)
        
    def _store_rdfobject(self, id, dsid, rdfobject):
        """Stores either an RDFobject or a Manifest object. In fact, any object that outputs
        RDF/XML from a .to_string() method will work."""
        resp, content = self.f.putString(id, dsid, rdfobject.to_string().encode('utf-8'),
    params={'dsLabel':dsid}, headers={'Content-Type':'application/rdf+xml'} )
        if resp.status not in [200, 201, 204]:
            raise FedoraStoreFailure(resp, content, "Store RDFobject to %s/%s" % (id, dsid))
    
    def _get_dsid_string(self, id, dsid):
        resp, content = self.f.getDatastream(id, dsid)
        if resp.status not in [200, 201, 204]:
            raise FedoraStoreFailure(resp, content, "Get RDFobject from %s/%s" % (id, dsid))
        else:
            return content

    def _store_dsid_string(self, id, dsid, bytestream, params, headers={"Content-Type":"text/plain"}):
        """Stores a bytestream - note the default content mimetype can (and likely should) be overridden."""
        resp, content = self.f.putString(id, dsid, bytestream,
                                            params=params,
                                            headers=headers )
        if resp.status not in [200, 201, 204]:
            raise FedoraStoreFailure(resp, content, "Store dsid bytestream to %s/%s" % (id, dsid))

    def _get_rdfobject(self, id, dsid):
        content = self._get_dsid_string(id, dsid)
        root = RDFobject()
        r.from_string(self.uri_base[id], content.decode('utf-8'))
        return r
        
    def _get_manifest(self, id, dsid):
        content = self._get_dsid_string(id, dsid)
        root = Manifest(self.uri_base["%s/%s" % (id, dsid)])
        r.from_string(content.decode('utf-8'))
        return r

    def getObject(self, id=None, create_if_doesnt_exist=True, namespace="entity"):
        if not id:
            if namespace:
                pid = self.f.getNextPID(namespace=namespace)
            else:
                pid = self.f.getNextPID()
            return self._create(pid)
        elif self.exists(id):
            return FedoraStoredObject(id, self)
        elif create_if_doesnt_exist:
            return self._create(id)
        else:
            raise ObjectNotFoundException
            
    def createObject(self, id):
        if self.exists(id):
            raise ObjectAlreadyExistsException
        else:
            return self._create(id)


class FedoraStoredObject(object):
    def __init__(self, id, fedoraclient):
        self.fs = fedoraclient
        self.id = id
        self.uri = self.fs.uri_base[id]
        self.root_uri = self.fs.uri_base["%s/%s" % (id, self.fs.root_dsid)]
        self.manifest_uri = self.fs.uri_base["%s/%s" % (id, self.fs.manifest_dsid)]
    def putRoot(self, rdf):
        return self.fs._store_rdfobject(self.id, self.fs.root_dsid, rdf)
    def getRoot(self):
        return self.fs._get_rdfobject(self.id, self.fs.root_dsid)
    def putManifest(self, rdf):
        return self.fs._store_rdfobject(self.id, self.fs.manifest_dsid, rdf)
    def getManifest(self):
        return self.fs._get_manifest(self.id, self.fs.manifest_dsid)
    
    def add_part(self, partid, bytestream, mimetype="text/plain", params={}, headers={}):
        headers["Content-Type"] = mimetype
        return self.fs._store_dsid_string(id, partid, bytestream, params, headers={"Content-Type":"text/plain"})
    
    def get_part(self, partid):
        return self.fs._get_dsid_string(self.id, partid)
        
    def del_part(self, partid):
        return self.fs._del_part(self.id, partid)
    
    def listParts(self):
        pass
    
