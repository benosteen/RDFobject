#!/usr/bin/python
# -*- coding: utf-8 -*-

from rdfobject import URIHelper, NAMESPACES

from rdfobject.constructs import NamedGraphNotFoundException

from datetime import datetime

TOPLEVEL_AIISO_ORGS = [u'Center',
                       u'College',
                       u'Department',
                       u'Division',
                       u'Faculty',
                       u'Institute',
                       u'Institution', # An Institution is the upper most level of an academic institution.
                       u'ResearchGroup',
                       u'School',
                       u'Organisation'
                       ]

class OrganisationUnit(object):
    def __init__(self, entity):
        self.entity = entity
        self.entity.add_namespace(u'aiiso', u'http://purl.org/vocab/aiiso/schema#')
        self.entity.add_namespace(u'foaf', u'http://xmlns.com/foaf/0.1/')
        self._set_from_entity()
        self.add_triple = self.entity.add_triple
        self.del_triple = self.entity.del_triple
        self.add_namespace = self.entity.add_namespace
        self.del_namespace = self.entity.del_namespace
    
    def _set_from_entity(self):
        if len(self.entity.types) > 0:
            self.type = self.entity.types[0]
        self.revert()
        
    def set_type(self, organisational_type="Organisation"):
        if organisational_type in TOPLEVEL_AIISO_ORGS:
            if organisational_type == 'Organisation':
                self.entity.root.set_type("foaf:%s" % organisational_type)
            else:
                self.entity.root.set_type("aiiso:%s" % organisational_type)

    def list_assertion_groups(self):
        return self.entity.parts
    
    def commit(self):
        self.entity.commit()
        
    def revert(self):
        self.entity.revert()

    def get_assertion_group(self, id=None, valid_from=datetime.now(), valid_until=None):
        return self.entity.add_named_graph(id, valid_from, valid_until)
    
    def is_assertion_group_valid(self, uri, date=None):
        """Leave date equal to None to check against the current date."""
        uri = self.entity.uh.parse_uri(uri)
        if uri in self.entity.parts:
            g = self.entity.manifest.get_graph()
            validfrom = None
            validuntil = None
            for s,p,o in g.triples((uri, 
                                    self.entity.uh.parse_uri("ov:validFrom"),
                                    None
                                    )):
                validfrom = self.entity.uh.literal_datetime_to_obj(o)

            for s,p,o in g.triples((uri, 
                                    self.entity.uh.parse_uri("ov:validUntil"),
                                    None
                                    )):
                validuntil = self.entity.uh.literal_datetime_to_obj(o)

            if not date:
                date = datetime.now()
            
            if validfrom and date>=validfrom:
                if not validuntil:
                    return True
                else:
                    if date<=validuntil:
                        return True
                    else:
                        return False
                
        

    def _set_valid_from(self, assertion_uri, date=datetime.now()):
        if assertion_uri in self.entity.parts:
            self.entity.parts_objs[assertion_uri].del_triple("ov:validFrom")
            self.entity.parts_objs[assertion_uri].add_triple("ov:validFrom", date)
            
    def _set_valid_until(self, assertion_uri, date=datetime.now()):
        if assertion_uri in self.entity.parts:
            self.entity.parts_objs[assertion_uri].del_triple("ov:validUntil")
            self.entity.parts_objs[assertion_uri].add_triple("ov:validUntil", date)
