#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
# add rdfobject to the path, if running in the test dir
if os.path.isdir(os.path.join(os.getcwd(), 'rdfobject')):
    sys.path.append(os.getcwd())
else:
    parent_dir = os.path.abspath(os.path.join(os.getcwd(), '..'))
    if os.path.isdir(os.path.join(parent_dir, 'rdfobject')):
        sys.path.append(parent_dir)
    else:
        print "Test must be run in either the test directory or the directory above it"
        quit

from rdfobject import *

print "+@"*30
print "Build + serialise Test"

r = RDFobject()

r.set_uri(u"info:fedora/ora:1")

r.add_namespace(u'foaf', u"http://xmlns.com/foaf/0.1/")
r.add_type(u'foaf:Agent')
r.add_namespace(u'dc', u"http://purl.org/dc/elements/1.1/")
r.add_namespace(u'dcterms', u"http://purl.org/dc/terms/")

r.add_triple(u'dc:title', u'Thesis')
r.add_triple(u'dc:description', u'Wrong Description')
r.add_triple(u'dc:description', u'An okay Description')
r.del_triple(u'dc:description', u'Wrong Description')
r.add_triple(u'dc:description', u'Best Description')
r.add_triple(u'dcterms:creator', u'http://registry.ouls.ox.ac.uk/p:10230')
r.add_triple(u'foaf:depiction', u'http://registry.ouls.ox.ac.uk/p:10230/thumbnail.jpg')

print r.to_string()

print r.to_string(format='n3')

print "+@"*30
print "wildcard object delete Test"

r.del_triple(u'dc:description')
r.add_triple(u'dc:description', u'Better Description')

print r.to_string(format='n3')

print "+@"*30
print "PARSE Test"

text = u"""<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF
   xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmlns:dcterms="http://purl.org/dc/terms/"
   xmlns:foaf="http://xmlns.com/foaf/0.1/"
   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
>
  <rdf:Description rdf:about="info:fedora/ora:1">
    <foaf:depiction rdf:resource="http://registry.ouls.ox.ac.uk/p:10230/thumbnail.jpg"/>
    <dc:description>Test Description</dc:description>
    <dcterms:creator rdf:resource="http://registry.ouls.ox.ac.uk/p:10230"/>
    <dc:title>Thesis</dc:title>
    <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Agent"/>
  </rdf:Description>
</rdf:RDF>
"""

text = text.encode('utf-8')
r.from_string(u"info:fedora/ora:1", text, encoding='utf-8')

print r.to_string(format='n3')

print "+@"*30
print "Remote URI PARSE Test"

r.from_url(u"http://databank.ouls.ox.ac.uk:8080/fedora/get/dataset:1/RELS-EXT", "info:fedora/dataset:1")

print r.to_string(format='n3')

print "+@"*30
print "Conjoining sparse rdfobjects for the same object"

r = RDFobject()

r.set_uri(u"info:fedora/ora:1")

r.add_namespace(u'foaf', u"http://xmlns.com/foaf/0.1/")
r.add_type(u'foaf:Agent')
r.add_namespace(u'bio', u"http://purl.org/vocab/bio/")
r.add_triple(u'foaf:depiction', u'http://farm4.static.flickr.com/3009/2898274035_9060edde03.jpg')
r.add_triple(u'foaf:birthday', u"11-09-1979")
r.add_triple(u'foaf:name', u"Ben O'Steen")

print "Before"
print "OBJECT -> r"
print r.to_string(format='n3')

p = RDFobject()

p.set_uri(u"info:fedora/ora:1")

p.add_namespace(u'sioc', u"http://rdfs.org/sioc/ns#")

p.add_triple(u'sioc:creator_of', u"http://oxfordrepo.blogspot.com")
p.add_triple(u'sioc:creator_of', u"http://www.flickr.com/photos/ben_on_the_move")

print "OBJECT -> p"

print p.to_string(format='n3')

print "-="*20

r.add_rdfobject(p)

print "After joining p to r [r.add_rdfobject(p)]:"

print r.to_string(format='n3')



