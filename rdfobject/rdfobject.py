#!/usr/bin/python
# -*- coding: utf-8 -*-

import rdflib
from rdflib import Namespace, URIRef, Literal
from rdflib import ConjunctiveGraph

from xml.sax.xmlreader import InputSource

from StringIO import StringIO

from urihelper import URIHelper, NAMESPACES

import re

# parse the P and Literal part of a encoded N3 line
NTHREE_PL_P = re.compile(r'([^\s]+?):([^\s]+?)\s*"([^\s]+)"\s*\;?$')
# parse the P and URIRef part of a N3 line
NTHREE_PURI_P = re.compile(r'([^\s]+?):([^\s]+?)\s*([^\s]+?):([^\s]+?)\s*\;?$')

class URINotSetException(Exception):
    """The URI has not been set. This object cannot be serialised or otherwise transcribed with the given value."""
    pass
    
class N3NotUnderstoodException(Exception):
    """The line of N3 encoded text was not understood"""
    pass

class TextInputSource(InputSource, object):
    def __init__(self, text, system_id=None):
        super(TextInputSource, self).__init__(system_id)
        self.url = system_id
        file = StringIO(text)
        self.setByteStream(file)
        # TODO: self.setEncoding(encoding)

    def __repr__(self):
        return self.url

def _cause_new_revision(fn):
    def new(self, *args, **kw):
        if not self.altered:
            self.altered = True
        return fn(self, *args, **kw)
    return new

class RDFobject(object):
    def __init__(self, uri=None):
        self.reset()
        if uri:
            self.set_uri(uri)
    
    def reset(self):
        self.namespaces = {}
        self.triples = set([])
        self.types = set([])
        self.g = None
        self.altered = False
        self._cached = False
        #add defaults
        self.urihelper = URIHelper(self.namespaces)
        self.add_namespace(u'rdf', u'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        self.add_namespace(u'rdfs', u"http://www.w3.org/2000/01/rdf-schema#")
        self.add_namespace(u'dcterms', u"http://purl.org/dc/terms/")
        self.add_namespace(u'ov', u'http://open.vocab.org/terms/')
        self.add_namespace(u'ore', u'http://www.openarchives.org/ore/terms/')
    
    @_cause_new_revision
    def add_type(self, uri_of_type):
        uri = self.urihelper.parse_uri(uri_of_type)
        self.types.add(uri)

    def set_type(self, uri_of_type):
        """Clears all other types to set this to be singularly-typed"""
        self.types = set([])
        self.add_type(uri_of_type)

    @_cause_new_revision
    def del_type(self, uri_of_type):
        uri = self.urihelper.parse_uri(uri_of_type)
        if uri in self.types:
            self.types.remove(uri)
    
    def set_uri(self, uri):
        self.uri = self.urihelper.parse_uri(uri)
    
    def add_namespace(self, prefix, uri):
        self.namespaces[prefix] = self.urihelper.get_namespace(uri)
        if prefix not in self.urihelper.namespaces:
            self.urihelper.namespaces[prefix] = self.urihelper.get_namespace(uri)

    def del_namespace(self, prefix):
        if prefix in self.namespaces:
            del self.namespaces[prefix]

    def triple_exists(self, predicate, objectRef):
        if not isinstance(objectRef, URIRef) and not isinstance(objectRef, Literal):
            objectRef = self.urihelper.parse_uri(objectRef, return_Literal_not_Exception=True)
        predicate_uri = self.urihelper.parse_uri(predicate)
        return (predicate_uri, objectRef) in self.triples

    def list_objects(self, predicate):
        predicate_uri = self.urihelper.parse_uri(predicate)
        return [x[1] for x in self.triples if x[0] == predicate_uri]

    @_cause_new_revision    
    def add_triple(self, predicate, objectRef):
        if not isinstance(objectRef, URIRef) and not isinstance(objectRef, Literal):
            objectRef = self.urihelper.parse_uri(objectRef, return_Literal_not_Exception=True)
        predicate_uri = self.urihelper.parse_uri(predicate)
        
        if (predicate_uri, objectRef) not in self.triples:
            if predicate_uri == NAMESPACES['rdf']['type']:
                self.add_type(objectRef)
            else:
                self.triples.add((predicate_uri, objectRef))

    @_cause_new_revision    
    def del_triple(self, predicate, objectRef=None):
        predicate_uri = self.urihelper.parse_uri(predicate)
        if objectRef:
            if not isinstance(objectRef, URIRef) and not isinstance(objectRef, Literal):
                objectRef = self.urihelper.parse_uri(objectRef, return_Literal_not_Exception=True)
            if (predicate_uri, objectRef) in self.triples:
                self.triples.remove((predicate_uri, objectRef))
        else:
            self.triples = set([t for t in self.triples if t[0] != predicate_uri])

    @_cause_new_revision
    def add_n3_triple(self, text):
        if NTHREE_PL_P.search(text):
            prefix, predicate, objectRef = NTHREE_PL_P.search(text).groups()
            objectRef = Literal(objectRef)
            self.add_triple(prefix, predicate, objectRef)
        elif NTHREE_PURI_P.search(text):
            prefix, predicate, obj_prefix, objectRef = NTHREE_PURI_P.search(text).groups()
            if obj_prefix not in ['http', 'info', 'urn', 'ftp', 'https']:
                self.add_triple(self.urihelper.uriref_shorthand_uri(prefix, predicate), self.urihelper.uriref_shorthand_uri(obj_prefix, objectRef))
            else:
                self.add_triple( self.urihelper.uriref_shorthand_uri(prefix, predicate), self.urihelper.parse_uri(":".join([obj_prefix, objectRef]), return_Literal_not_Exception=True) )
        else:
            raise N3NotUnderstoodException()

    def from_string(self, uri, text, format="xml", encoding="utf-8"):
        self.reset()
        self.set_uri(uri)
        t = TextInputSource(text, system_id=uri)
        t.setEncoding(encoding)
        g = ConjunctiveGraph(identifier=self.uri)
        g = g.parse(t, format)
        for prefix, ns in g.namespaces():
            self.add_namespace(prefix, ns)
        for s,p,o in g.triples((self.uri, None, None)):
            self.add_triple(p, o)

    
    def from_url(self, url, uri=None, format="xml",  encoding="utf-8"):
        self.reset()
        if not uri:
            self.set_uri(url)
        else:
            self.set_uri(uri)
        g = ConjunctiveGraph(identifier=self.uri)
        g = g.parse(url, format)
        for prefix, ns in g.namespaces():
            self.add_namespace(prefix, ns)
        for s,p,o in g.triples((self.uri, None, None)):
            self.add_triple(p, o)
    
    def get_graph(self):
        if not self.uri:
            raise URINotSetException()
        g = ConjunctiveGraph(identifier=self.uri)
        
        for ns in self.namespaces:
            g.bind(ns, self.namespaces[ns])
        #add global prefix bindings
        for ns in self.urihelper.namespaces:
            g.bind(ns, self.urihelper.namespaces[ns])
            
        # Add type(s)
        for type in self.types:
            g.add((self.uri, self.namespaces['rdf']['type'], type))
        
        for triple in self.triples:
            g.add((self.uri, triple[0], triple[1]))
        return g

    def list_triples(self):
        """output a list of the triple tuples - Should really make this a generator, but anyway."""
        triples = []
        # Add type(s)
        for type in self.types:
            triples.append((self.uri, self.namespaces['rdf']['type'], type))
        
        for triple in self.triples:
            triples.append((self.uri, triple[0], triple[1]))
        return triples

    @_cause_new_revision
    def add_rdfobject(self, rdfobject):
        """ ** NOTE ** This only adds the property and object pairs, and discards the subject """
        self._add_graph(rdfobject.get_graph())

    def _add_graph(self, g):
        """ ** NOTE ** This only adds the property and object pairs, and discards the subject """
        for prefix, ns in g.namespaces():
            self.add_namespace(prefix, ns)
        for s,p,o in g.triples((None, None, None)):
            self.add_triple(p, o)

    @_cause_new_revision
    def munge_graph(self, g):
        """ This will only add the triples that have this object's subject as their subject. """
        for prefix, ns in g.namespaces():
            self.add_namespace(prefix, ns) 
        for s,p,o in g.triples((self.uri, None, None)):
            self.add_triple(p, o)
    
    def __str__(self):
        return self.to_string('xml')
    
    def to_string(self, format="xml"):
        return self.get_graph().serialize(format=format, encoding="utf-8")+"\n"
        

