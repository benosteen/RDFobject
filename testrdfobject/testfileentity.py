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

from rdfobject import FileEntityFactory, NAMESPACES

f = FileEntityFactory(uri_base=u"info:fedora/", storage_dir="fileentitytest", prefix="_")

uri=u"info:fedora/ora:1"

dsid_root = u"info:fedora/ora:1/%s"

entity = f.get(uri)

entity.add_namespaces(NAMESPACES)

entity.add_triple(uri, "dcterms:creator", "http://me.example.org/benosteen")
entity.add_triple(uri, "dcterms:requires", dsid_root % "RELSINT")
entity.add_triple(uri, "dc:subject", "testobject")

entity.add_triple(dsid_root % "RELSINT", "dc:creator", "Ben O'Steen")
entity.add_triple(dsid_root % "DC", "dc:creator", "Ben O'Steen")
entity.add_triple(dsid_root % "Image.jpg", "dc:creator", "Ben O'Steen")
entity.add_triple(dsid_root % "Image.jpg", "dc:format", "image/jpg")
entity.add_triple("http://me.example.org/benosteen", "foaf:depiction", dsid_root % "Image.jpg")

entity.commit()

print "-=-"*20
print entity.root.to_string()
print "-=-"*20
print entity.manifest.to_string()

entity.add_triple(uri, "dc:subject", "adding test")
entity.add_triple(uri, "foaf:birthday", "11-09-1979")
entity.commit()


print "-=-"*20
print entity.root.to_string()


entity.add_triple(dsid_root % "Image2.jpg", "dc:creator", "Ben O'Steen")
entity.add_triple(dsid_root % "Image2.jpg", "dc:format", "image/jpg")
entity.add_triple(dsid_root % "Image.jpg", "dc:description", "Image of Ben")
entity.add_triple("http://me.example.org/benosteen", "foaf:depiction", dsid_root % "Image2.jpg")
print "-=-"*20
entity.commit()

t = entity.add_named_graph("test")
t.add_namespace(u'foaf', u"http://xmlns.com/foaf/0.1/")
t.add_triple(uri, "foaf:name", "Ben O'Steen")

print t.uri

#print "-=-"*20
#print t.to_string()

entity.commit()
entity.commit()
entity.commit()
entity.commit()


