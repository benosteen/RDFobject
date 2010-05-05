#!/usr/bin/python
# -*- coding: utf-8 -*-

from rdfobject.constructs import Entity

from rdfobject import RDFobject, NAMESPACES

from rdfobject.constructs import Manifest

from rdfobject.stores import ItemDoesntExistException

from rdflib import ConjunctiveGraph

from collections import defaultdict

from datetime import datetime

import simplejson

import logging

def _init_obj_wrapper(fn):
    def new(self, *args, **kw):
        if not self.obj:
            self.context = defaultdict(list)
            self.obj = self.s.getObject(self.id)
            self.uri = self.obj.uri
        return fn(self, *args, **kw)
    return new

class StoredEntity(Entity):
    def init(self, id=None, storageclient=None, **logcontext):
        self.id = id
        self.s = storageclient
        self.obj = None
        self.logcontext = logcontext
        self.revert()

    @_init_obj_wrapper
    def commit(self):
        self.store_root()
        self.store_manifest()
        self.store_parts()
        self.s.log_audit(self.id, self.logcontext, self.context)
        # Change delta logged...
        self.context = defaultdict(list)

    @_init_obj_wrapper
    def add_namespace(self, prefix, ns):
        super(StoredEntity, self).add_namespace(prefix, ns)
        self.context['addnamespace'].append((prefix, ns))

    @_init_obj_wrapper
    def del_namespace(self, prefix):
        super(StoredEntity, self).del_namespace(prefix)
        self.context['delnamespace'].append((prefix, ns))
        
    @_init_obj_wrapper
    def add_triple(self, s,p,o, create_item=True):
        super(StoredEntity, self).add_triple(s,p,o, create_item=create_item)
        self.context['add'].append((s,p,o.__str__()))
        
    @_init_obj_wrapper
    def del_triple(self, s,p,o=None):
        super(StoredEntity, self).del_triple(s,p,o)
        self.context['del'].append((s,p,o.__str__()))
        
    @_init_obj_wrapper
    def add_type(self, uritype):
        super(StoredEntity, self).add_type(uritype)
        self.context['addtype'].append(uritype)
        
    @_init_obj_wrapper
    def del_type(self, uritype):
        super(StoredEntity, self).del_type(uritype)
        self.context['deltype'].append(uritype)

    @_init_obj_wrapper
    def list_parts(self):
        return self.obj.list_parts()
        
    @_init_obj_wrapper
    def list_part_versions(self, part_id):
        return self.obj.list_part_versions(part_id)
        
    @_init_obj_wrapper
    def del_part_version(self, part_id, version):
        r = self.obj.del_part_version(part_id, version)
        version_uri = self.uh.parse_uri("%s/%s/%s" % (self.uri, part_id, version))
        part_uri = self.uh.parse_uri("%s/%s" % (self.uri, part_id))
        try:
            self.del_triple(part_uri, "dcterms:hasVersion", version_uri)
        except Exception, e:
            print "Fail %s " % e
        try:
            self.manifest.del_item(version_uri)
        except Exception, e:
            print "Fail %s " % e
        self.commit()
        return r

    @_init_obj_wrapper
    def del_part_versions(self, part_id, versions, force=False):
        r = self.obj.del_part_versions(part_id, versions, force)
        return r

    @_init_obj_wrapper
    def remove_previous_versions(self, part_id):
        versions = self.obj.list_part_versions(part_id)
        versions.sort()
        most_current = versions.pop()
        self.del_part_versions(part_id, versions)
        return most_current

    @_init_obj_wrapper
    def revert(self, create_if_nonexistent=True):
        self.load_root(create_if_nonexistent)
        self.load_manifest(create_if_nonexistent)
        # reset mimetypes for core manifest
        try:
            self.manifest.del_triple("%s/%s" % (self.uri, "ROOT"), "dc:format", None)
        except:
            pass
        try:
            self.manifest.del_triple("%s/%s" % (self.uri, "MANIFEST"), "dc:format", None)
        except:
            pass
        self.manifest.add_triple("%s/%s" % (self.uri, "ROOT"), "dc:format", "application/rdf+xml")
        self.manifest.add_triple("%s/%s" % (self.uri, "MANIFEST"), "dc:format", "application/rdf+xml")
        self.context = defaultdict(list)

    @_init_obj_wrapper
    def store_root(self):
        # only store the root if it has changed:
        if self.root.altered:
            return self.obj.putRoot(self.root)

    @_init_obj_wrapper
    def load_root(self, create_if_nonexistent=True):
        self.root = self.obj.getRoot()

    @_init_obj_wrapper
    def put_stream(self, part_id, bytestream, mimetype=None, version=None, commit_metadata_changes=True):
        response = self.obj.add_part(part_id, bytestream, version=version, mimetype=mimetype)
        version_uri = self.uh.parse_uri("%s/%s/%s" % (self.uri, part_id, response['version']))
        part_uri = self.uh.parse_uri("%s/%s" % (self.uri, part_id))
        self.add_triple(self.uri, "ore:aggregates", part_uri)
        self.add_triple(part_uri, "dcterms:hasVersion", version_uri)
        self.add_triple(part_uri, "dcterms:isPartOf", self.uri)
        self.add_triple(version_uri, "dcterms:modified", datetime.now())
        self.del_triple(part_uri, "dcterms:modified", None)
        self.add_triple(part_uri, "dcterms:modified", datetime.now())
        if mimetype:
            self.del_triple(part_uri, "dc:format", None)
            self.add_triple(part_uri, "dc:format", mimetype)
            self.add_triple(version_uri, "dc:format", mimetype)
        if response.get('checksum',None):
            self.del_triple(part_uri, "ov:hasChecksum", None)
            self.add_triple(part_uri, "ov:hasChecksum", "%s:%s" % response['checksum'])
            self.add_triple(version_uri, "ov:hasChecksum", "%s:%s" % response['checksum'])
            
        if commit_metadata_changes:
            self.commit()
        return response

    @_init_obj_wrapper
    def get_stream_metadata(self, part_id):
        part_uri = self.uh.parse_uri("%s/%s" % (self.uri, part_id))
        try:
            return self.manifest.get_item(part_uri)
        except ItemDoesntExistException:
            return

    @_init_obj_wrapper
    def del_stream(self, part_id, commit_metadata_changes=True):
        for version in self.list_part_versions(part_id):
            self.del_part_version(part_id, version)
        self.obj.del_part(part_id)
        part_uri = self.uh.parse_uri("%s/%s" % (self.uri, part_id))
        self.del_triple(self.uri, "ore:aggregates", part_uri)
        # Try to remove any triples where this part was the subject
        for uri in self.manifest.items:
            if uri.startswith(part_uri):
                try:
                    self.manifest.del_item(uri)
                except:
                    print "Failed on %s" % uri
        if commit_metadata_changes:
            self.commit()

    @_init_obj_wrapper
    def get_stream(self, part_id, version=None):
        stream = self.obj.get_part(part_id, stream=True, version=version)
        return stream

    @_init_obj_wrapper
    def get_as_bytes(self, part_id, version=None):
        stream = self.obj.get_part(part_id, stream=False, version=version)
        return stream

    @_init_obj_wrapper
    def store_parts(self):
        for part_uri in self.parts:
            if part_uri.startswith(self.obj.uri) and self.parts_objs[part_uri].altered:
                part_id = part_uri[len(self.obj.uri)+1:]
                self.put_stream(part_id, self.parts_objs[part_uri].to_string(),
                                mimetype="application/rdf+xml")

    @_init_obj_wrapper
    def store_manifest(self):
        # only store the manifest if it has changed:
        if self.manifest.altered:
            return self.obj.putManifest(self.manifest)

    @_init_obj_wrapper
    def load_manifest(self, create_if_nonexistent=True):
        self.manifest = self.obj.getManifest()
        g = self.manifest.get_graph()
        if isinstance(g, ConjunctiveGraph):
            for s,p,o in g.triples(( None, NAMESPACES['foaf']['primaryTopic'], self.root.uri)):
                if s not in self.parts:
                    self.parts.add(s)
                    if s.startswith(self.obj.uri):
                        part_id = s[len(self.obj.uri)+1:]
                        r = Manifest(s)
                        r.from_string(self.obj.get_part(part_id))
                        self.parts_objs[s] = r
                    elif s.startswith("http://"):
                        r = Manifest(s)
                        r.from_url(s)
                        self.parts_objs[s] = r

    @_init_obj_wrapper
    def add_named_graph(self, graph_id, valid_from=None, valid_until=None):
        graph_uri = self.uh.parse_uri("%s/%s" % (self.uri, graph_id))
        if graph_uri not in self.parts:
            g = super(StoredEntity, self).add_named_graph(graph_id, valid_from=valid_from, valid_until=valid_until)
            self.obj.add_part(graph_id, g.to_string())
            self.commit()
            return g
        else:
            return self.parts_objs[graph_uri]

    @_init_obj_wrapper
    def del_named_graph(self, graph_id):
        super(StoredEntity, self).del_named_graph(graph_id)
        self.obj.del_part(graph_id)
        self.commit()

