#!/usr/bin/python
# -*- coding: utf-8 -*-

import rdflib
from rdflib import Namespace, URIRef, Literal
from datetime import datetime
import re

# spot a URI/resource string (crudely, but whatever)
URI_P = re.compile(r'^http\:|^urn\:|^info\:|^ftp\:|^https\:')
# parse shorthand URIs like foaf:Agent into ('foaf', 'agent')
URI_SHORT = re.compile(r'^([^:]+):([^:]+)$')

# A few default namespaces
NAMESPACES = {}
NAMESPACES['rdf'] = Namespace(u'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
NAMESPACES['rdfs'] = Namespace(u'http://www.w3.org/2000/01/rdf-schema#')
NAMESPACES['dc'] = Namespace(u'http://purl.org/dc/elements/1.1/')
NAMESPACES['dcterms'] = Namespace(u'http://purl.org/dc/terms/')
NAMESPACES['foaf'] = Namespace(u'http://xmlns.com/foaf/0.1/')
NAMESPACES['ov'] = Namespace(u'http://open.vocab.org/terms/')

class NotANamespaceException(Exception):
    """An attempt to get a namespace was made and the URI didn't end in # or /"""
    pass

class PrefixNotKnownException(Exception):
    """The prefix used is not in the list of known Namespaces - the namespace can be added before serialisation however."""
    pass
class URINotSetException(Exception):
    """The URI has not been set. This object cannot be serialised or otherwise transcribed with the given value."""
    pass
    
class URIHelper:
    """ NB singleton """

    class __impl:
        """ Implementation of the singleton interface """
        def __init__(self, namespaces):
            if not namespaces:
                self.namespaces = {}
                for ns in NAMESPACES:
                    self.namespaces[ns] = NAMESPACES[ns]
            else:
                self.namespaces = namespaces

        def add_namespace(self, prefix, ns):
            if isinstance(ns, Namespace):
                self.namespaces[prefix] = ns
            else:
                self.namespaces[prefix] = Namespace(ns)

        def literal_datetime_to_obj(self, lit_datetime):
            l = lit_datetime.toPython()
            if isinstance(l, Literal):
                l = datetime.strptime(l.split('.')[0],"%Y-%m-%dT%H:%M:%S")
            return l

        def parse_uri(self, rdf_text, return_Literal_not_Exception=False):
            if isinstance(rdf_text, URIRef):
                return rdf_text
            elif isinstance(rdf_text, basestring):
                if URI_P.match(rdf_text.strip()):
                    return URIRef(rdf_text.strip())
                elif URI_SHORT.match(rdf_text.strip()):
                    prefix, tail = URI_SHORT.match(rdf_text.strip()).groups()
                    try:
                        return self.uriref_shorthand_uri(prefix, tail)
                    except PrefixNotKnownException:
                        if return_Literal_not_Exception:
                            return Literal(rdf_text)
                        else:
                            raise URINotSetException
            if return_Literal_not_Exception:
                return Literal(rdf_text)
            else:
                raise URINotSetException
                    
        def get_uriref(self, rdf_text, force=False):
            """Similar to parse_uri, but no attempt is made to expand prefixes"""
            if isinstance(rdf_text, URIRef):
                return rdf_text
            elif isinstance(rdf_text, basestring):
                if URI_P.match(rdf_text.strip()):
                    return URIRef(rdf_text.strip())
            elif force:
                # Force a URIRef to be created
                return URIRef(rdf_text.strip())
            # Not a URIRef nor, recognised as a URI in text.
            raise URINotSetException()

        def get_namespace(self, namespace_uri):
            if namespace_uri.endswith('/') or namespace_uri.endswith('#'):
                return Namespace(self.get_uriref(namespace_uri))
            elif namespace_uri == URIRef("http://www.w3.org/XML/1998/namespace"):
                # Not an RDF namespace, but an artifact of the RDF/XML parsing
                return Namespace(self.get_uriref(namespace_uri))
            else:
                raise NotANamespaceException()

        def uriref_shorthand_uri(self, prefix, tail):
            if prefix not in self.namespaces:
                raise PrefixNotKnownException()
            else:
                return self.namespaces[prefix][tail]
        

    # storage for the instance reference
    __instance = None

    def __init__(self, namespaces=None):
        """ Create singleton instance """
        # Check whether we already have an instance
        if URIHelper.__instance is None:
            # Create and remember instance
            URIHelper.__instance = URIHelper.__impl(namespaces)

        # Store instance reference as the only member in the handle
        self.__dict__['_URIHelper__instance'] = URIHelper.__instance

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)
