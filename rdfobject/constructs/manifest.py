#!/usr/bin/python
# -*- coding: utf-8 -*-

from rdfobject import *

import rdflib
from rdflib import ConjunctiveGraph

class ItemAlreadyExistsException(Exception):
    """The Item already is listed in the manifest"""
    pass

class ItemDoesntExistException(Exception):
    """There is no record of this item in the Manifest"""
    pass

def _altered_flag(fn):
    def new(self, *args, **kw):
        self.altered = True
        return fn(self, *args, **kw)
    return new


class Manifest(object):
    def __init__(self, uri=None):
        self.items = []
        self.items_rdfobjects = {}
        self.namespaces = {}
        self.altered = False
        self._output = False
        self.uh = URIHelper()
        if uri:
            self.uri = self.uh.parse_uri(uri)

    def __iter__(self):
        class Manifest_iter:
            def __init__(self, items, items_dict):
                self.items = items
                self.items_dict = items_dict
                self.last = 0
            def __iter__(self):
                return self
            def next(self):
                if self.last >= len(self.items):         # threshhold terminator
                    raise StopIteration
                elif len(self.items) == 0:
                    raise StopIteration
                else:
                    self.last += 1
                    return self.items_dict[self.items[self.last-1]]
        return Manifest_iter(self.items, self.items_rdfobjects)

    # @_altered_flag
    def add_namespace(self, prefix, ns):
        self.namespaces[prefix] = self.uh.get_namespace(ns)
        if prefix not in self.uh.namespaces:
            self.uh.namespaces[prefix] = self.uh.get_namespace(ns)
        for item in self.items_rdfobjects:
            self.items_rdfobjects[item].add_namespace(prefix, ns)

    # @_altered_flag
    def del_namespace(self, prefix):
        if prefix in self.namespaces:
            del self.namespaces[prefix]
            for item in self.items_rdfobjects:
                self.items_rdfobjects[item].del_namespace(prefix)

    @_altered_flag
    def from_string(self, rdf_manifest_string, format="xml"):
        t = TextInputSource(rdf_manifest_string)
        g = ConjunctiveGraph()
        g = g.parse(t, format)
        
        for s,p,o in g.triples((None, None, None)):
            if s not in self.items:
                self.items.append(s)
            if p == NAMESPACES['rdf']['type']:
                self.items_rdfobjects.setdefault(s,RDFobject(uri=s)).add_type(o)
            else:
                self.items_rdfobjects.setdefault(s,RDFobject(uri=s)).add_triple(p, o)

        for prefix, ns in g.namespaces():
            self.add_namespace(prefix ,ns)
    
    def to_string(self, format="xml"):
        if self.altered == False and isinstance(self._output, rdflib.ConjunctiveGraph):
            return self._output.serialize(format=format) + "\n"
        self._output = self.get_graph()
        if isinstance(self._output, rdflib.ConjunctiveGraph):
            self.altered = False
            return self._output.serialize(format=format) + "\n"
        else:
            return u'<?xml version="1.0" encoding="UTF-8"?>\n'
    
    def get_graph(self):
        if self.items and self.items_rdfobjects:
            g = ConjunctiveGraph()
            # add bindings from the first graph:
            ns_list = self.items_rdfobjects[self.items[0]].namespaces
            for prefix in ns_list:
                g.bind(prefix, ns_list[prefix])
            #add global prefix bindings
            for ns in self.uh.namespaces:
                g.bind(ns, self.uh.namespaces[ns])
            
            for item in self.items_rdfobjects:
                for s,p,o in self.items_rdfobjects[item].list_triples():
                    g.add((s,p,o))
                self.items_rdfobjects[item].altered = False
            return g
        else:
            return ""
    
    def get_item(self, item_uri):
        r_uri = self.uh.parse_uri(item_uri)
        if r_uri not in self.items:
            raise ItemDoesntExistException()
        else:
            return self.items_rdfobjects[r_uri]

    @_altered_flag
    def add_item(self, item_uri):
        r_uri = self.uh.parse_uri(item_uri)
        if r_uri not in self.items:
            self.items_rdfobjects[r_uri] = RDFobject(item_uri)
            self.items.append(r_uri)
            for prefix in self.namespaces:
                self.items_rdfobjects[r_uri].add_namespace(prefix, self.namespaces[prefix])
        else:
            raise ItemAlreadyExistsException()

    @_altered_flag    
    def del_item(self, item_uri):
        r_uri = self.uh.parse_uri(item_uri)
        if r_uri in self.items:
            del self.items_rdfobjects[r_uri]
            self.items.remove(r_uri)
        else:
            raise ItemDoesntExistException()

    @_altered_flag
    def add_triple(self, s, p, o, create_item=True):
        s = self.uh.parse_uri(s)
        if s not in self.items:
            if create_item:
                self.add_item(s)
            else:
                raise ItemDoesntExistException()
        self.items_rdfobjects[s].add_triple(p,o)

    def triple_exists(self, s, p, o):
        if s and s != "*":
            s_uri = self.uh.parse_uri(s)
            if s_uri in self.items_rdfobjects:
                return self.items_rdfobjects[s_uri].triple_exists(p,o)
        return False

    def list_objects(self, s, p):
        if s == "*":
            construct = {}
            for s_uri in self.items_rdfobjects.keys():
                objs = self.items_rdfobjects[s_uri].list_objects(p)
                if objs:
                    construct[s_uri] = objs
            return construct
        s_uri = self.uh.parse_uri(s)
        if s_uri in self.items_rdfobjects:
            return self.items_rdfobjects[s_uri].list_objects(p)
        return []

    @_altered_flag
    def del_triple(self, s, p, o=None):
        """ NB To delete all of a certain property (p) in a given item (s), do not set (o)"""
        s = self.uh.parse_uri(s)
        if s in self.items:
            self.items_rdfobjects[s].del_triple(p,o)
        else:
            raise ItemDoesntExistException()
    
