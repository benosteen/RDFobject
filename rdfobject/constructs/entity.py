#!/usr/bin/python
# -*- coding: utf-8 -*-
from rdfobject import *
from rdfobject.constructs import Manifest

from datetime import datetime

class NamedGraphNotFoundException(Exception):
    pass

class Entity(object):
    def __init__(self, uri=None, manifest_uri=None):
        self._reset(uri, manifest_uri)
        self.uh = URIHelper()
    
    def _reset(self, uri, manifest_uri):
        self.parts = set([])
        self.parts_objs = {}
        self.root = RDFobject(uri)
        self.types = self.root.types
        if self.root.uri:
            self.uri = self.root.uri
        if manifest_uri:
            self.root.add_triple("dcterms:requires", manifest_uri)
        self.manifest = Manifest(manifest_uri)
        
    def add_namespaces(self, ns_dict):
        """Convenience method for adding namespaces"""
        for prefix in ns_dict:
            self.add_namespace(prefix, ns_dict[prefix])
        
    def add_namespace(self, prefix, ns):
        self.uh.add_namespace(prefix, ns)
        self.root.add_namespace(prefix, ns)
        self.manifest.add_namespace(prefix, ns)
        for part_uri in self.parts:
            self.parts_objs[part_uri].add_namespace(prefix, ns)
        
    def del_namespace(self, prefix):
        self.root.del_namespace(prefix)
        self.manifest.del_namespace(prefix)
        
    def add_triple(self, s,p,o, create_item=True):
        s = self.uh.parse_uri(s)
        if s == self.uri:
            self.root.add_triple(p,o)
        else:
            self.manifest.add_triple(s,p,o, create_item)

    def del_triple(self, s,p,o=None):
        s = self.uh.parse_uri(s)
        if s == self.uri:
            self.root.del_triple(p,o)
        else:
            self.manifest.del_triple(s,p,o)

    def add_type(self, uritype):
        self.root.add_type(uritype)

    def del_type(self, uritype):
        self.root.del_type(uritype)

    def list_aggregates(self):
        g = self.root.get_graph()
        agg = []
        for _,_,o in g.triples((None, self.uh.parse_uri("ore:aggregates"), None)):
            agg.append(o)
        return agg

    def __str__(self, format="xml"):
        return self.to_string(format)

    def get_graph(self):
        g = self.root.get_graph()
        g_m = self.manifest.get_graph()
        if g_m:
            for prefix, ns in g_m.namespaces():
                g.bind(prefix, ns)
            for s,p,o in g_m.triples((None, None, None)):
                g.add((s, p, o))
        return g
    
    def to_string(self, format="xml"):
        return self.get_graph().serialize(format=format, encoding="utf-8") + u"\n"

    def from_string(self, root_uri, rdfstring, format="xml"):
        t = TextInputSource(rdfstring)
        g = ConjunctiveGraph()
        g = g.parse(t, format)
        for prefix, ns in g.namespaces():
            self.add_namespace(prefix ,ns)
        for s,p,o in g.triples((None, None, None)):
            self.add_triple(s,p,o)

    def namedgraphid_to_uri(self, graph_id):
        return "%s/%s" % (self.uri, graph_id)

    def add_named_graph(self, graph_id, valid_from=datetime.now(), valid_until=None):
        uri = self.namedgraphid_to_uri(graph_id)
        if self.uh.parse_uri(uri) not in self.parts:
            r = Manifest(uri)
            
            self.parts.add(r.uri)
            self.parts_objs[r.uri] = r
            self.add_triple(r.uri, "rdf:type", "http://www.w3.org/2004/03/trix/rdfg-1/Graph")
            self.add_triple(r.uri, "dc:format", "application/rdf+xml")
            self.add_triple(r.uri, 'foaf:primaryTopic', self.uri)
            self.add_triple(r.uri, "dcterms:created", datetime.now())
            if valid_from:
                self.add_triple(r.uri, "ov:validFrom", valid_from)
            if valid_until:
                self.add_triple(r.uri, "ov:validUntil", valid_until)
            self.add_triple(self.uri, "ore:aggregates", r.uri)
            self.add_triple(r.uri, "dcterms:isPartOf", self.uri)
            return r
        else:
            return self.parts_objs[self.uh.parse_uri(uri)]

    def get_named_graph(self, graph_id, create_if_necessary=False):
        uri = self.namedgraphid_to_uri(graph_id)
        if self.uh.parse_uri(uri) not in self.parts:
            raise NamedGraphNotFoundException
        else:
            return self.parts_objs[self.uh.parse_uri(uri)]

    def del_named_graph(self, graph_id):
        uri = self.uh.parse_uri("%s/%s" % (self.uri, graph_id))
        if uri in parts:
            self.parts.remove(uri)
            del self.parts_objs[uri]
            self.del_triple(self.uri, "ore:aggregates", uri)
            self.manifest.del_item(uri)
