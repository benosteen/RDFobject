#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
FS Pairtree-RDF storage
==============

Conventions used:

Objects are stored as pairtree based on id, eg.

id = "01020304"  and base dir = "storage"

gives

physical directory for id = "storage/01/02/03/04/05"

FS convention for versionable items:

{id_path}/ROOT/_XXXX => Object RDF for this ID
{id_path}/MANIFEST/_XXXX => Manifest RDF for this ID
{id_path}/_1/_XXXX => Object RDF for this ID, subpart 1
{id_path}/_2/_XXXX => Object RDF for this ID, subpart 2
{id_path}/_3/_XXXX => Object RDF for this ID, subpart 3

XXXX is just an autoincrementing number - largest is the latest and the FS
contains the ctime and the mtime of the file.

# TODO - add a simple method to view version numbers, and delete them
# deletion will retain the sequence of course.
"""

import os, sys, shutil

import codecs

import string

from rdfobject import RDFobject

from pairtree import PairtreeStorageClient

from storage_exceptions import ObjectNotFoundException, ObjectAlreadyExistsException, \
                               NotAPairtreeStoreException, VersionNotFoundException, \
                               PartNotFoundException

from rdfobject.constructs import Manifest, ItemAlreadyExistsException, ItemDoesntExistException

from rdflib import Namespace

import simplejson

from datetime import datetime

import random

URI_BASE = "info:local/"
STORAGE_DIR = "./rdffilestore"
SPECIAL_FILE_PREFIX = "_"

class FileStorageFactory(object):
    def get_store(self, uri_base=URI_BASE, store_dir=STORAGE_DIR, prefix=SPECIAL_FILE_PREFIX,
    shorty_length=2, queue=None, hashing_type=None, **context):
        return FileStorageClient(uri_base, store_dir, prefix, shorty_length, queue, hashing_type, **context)

class FileStorageObject(object):
    def __init__(self, id, fs_store_client):
        self.fs = fs_store_client
        self.id = id
        self.uri = self.fs.uri_base[id]
        self.root_uri = self.fs.uri_base["%s/%s" % (id, u"ROOT")]
        self.manifest_uri = self.fs.uri_base["%s/%s" % (id, u"MANIFEST")]

    def putRoot(self, rdf):
        """Store the root for this object - rdf can either be
        an RDFXML string or an RDFobject"""
        if isinstance(rdf, RDFobject):
            return self.fs._store_rdfobject(self.id, u'ROOT', rdf)
        else:
            r = RDFobject(self.id).from_string(rdf)
            return self.fs._store_rdfobject(self.id, u'ROOT', rdf)

    def getRoot(self):
        """RDFObject for this object"""
        return self.fs._get_rdfobject(self.id, u'ROOT')

    def add_part(self, partid, bytestream, version=None, mimetype=None):
        return self.fs._put_part(self.id, partid, bytestream, version=version, mimetype=mimetype)

    def get_part(self, partid, stream=False, version=None):
        return self.fs._get_part(self.id, partid, stream, version)

    def del_part(self, partid):
        return self.fs._del_part(self.id, partid)

    def list_parts(self):
        return self.fs._list_parts(self.id)

    def list_part_versions(self, partid):
        return self.fs._list_part_versions(self.id, partid)

    def del_part_versions(self, partid, versions, force=False):
        response = {}
        for version in versions:
            try:
                response[version] = self.del_part_version(partid, version)
            except Exception, e:
                if force:
                    response[version] = False
                else:
                    raise e
        return response

    def del_part_version(self, partid, version):
        return self.fs._del_part_version(self.id, partid, version)

    def putManifest(self, rdf):
        """Store the manifest for this object - rdf can either be
        an RDFXML string or a Manifest"""
        if isinstance(rdf, Manifest):
            return self.fs._store_manifest(self.id, u'MANIFEST', rdf)
        else:
            r = Manifest().from_string(rdf)
            return self.fs._store_manifest(self.id, u'MANIFEST', rdf)

    def getManifest(self):
        """Manifest for this object"""
        return self.fs._get_manifest(self.id, u'MANIFEST', self.manifest_uri)


class FileStorageClient(object):
    def __init__(self, uri_base, store_dir, prefix, shorty_length,queue=None, hashing_type=None, **context):
        self.store_dir = store_dir
        self.uri_base = None
        if uri_base:
            self.uri_base = Namespace(uri_base)
        self.ids = {}
        self.id_parts = {}
        self.prefix = prefix
        self.shorty_length = shorty_length
        self.queue = queue
        self.context = context
        if hashing_type:
            self.hashing_type = hashing_type
            self.storeclient = PairtreeStorageClient(uri_base, store_dir, shorty_length,
                                                     hashing_type=self.hashing_type)
        else:
            self.storeclient = PairtreeStorageClient(uri_base, store_dir, shorty_length)
        if self.storeclient.uri_base:
            self.uri_base = Namespace(self.storeclient.uri_base)


    def list_ids(self):
        return self.storeclient.list_ids()

    def _get_latest_part(self, id, part_id):
        try:
            versions = self._list_part_versions(id, part_id)
            if versions:
                return max(versions)
            return 0
        except PartNotFoundException:
            return 0

    def _list_parts(self, id):
        return self.storeclient.list_parts(id)

    def _list_part_versions(self, id, part_id):
        if part_id in self.storeclient.list_parts(id):
            versions = self.storeclient.list_parts(id, part_id)
            numbered_versions = [int(x.split(self.prefix)[-1]) for x in versions]
            if numbered_versions:
                return numbered_versions
            else:
                return []
        else:
            raise PartNotFoundException

    def _del_part_version(self, id, part_id, version):
        if not self.storeclient.exists(id):
            raise ObjectNotFoundException
        if part_id in self.storeclient.list_parts(id):
            if version in self._list_part_versions(id, part_id):
                # delete version
                resp = self.storeclient.del_stream(id, "%s%s%s" % (part_id, self.prefix, version), path=part_id)
                if self.queue != None:
                    self._log(id, 'd', 'Deleting a version of a part', part_id=part_id, version=version)
                return resp
            else:
                raise VersionNotFoundException(part_id=part_id, version=version)
        else:
            raise PartNotFoundException

    def _put_part(self, id, part_id, bytestream, version=False, buffer_size = 1024 * 8, mimetype=None):
        if not self.storeclient.exists(id):
            self.storeclient.create_object(id)
        if not version:
            version = self._get_latest_part(id, part_id) + 1
        part_name = "%s%s%s" % (part_id, self.prefix, version)
        hexhash = self.storeclient.put_stream(id, part_id, part_name, bytestream, buffer_size)
        if self.queue != None:
            if version == 1:
                self._log(id, 'c', 'Creating a part', part_id=part_id, version=version, checksum=hexhash, mimetype=mimetype)
            else:
                self._log(id, 'w', 'Updating a part', part_id=part_id, version=version, checksum=hexhash, mimetype=mimetype)
        return {'version':version, 'checksum':hexhash}

    def _get_part(self, id, part_id, stream, version = False):
        if not self.storeclient.exists(id):
            raise ObjectNotFoundException
        if not version:
            version = self._get_latest_part(id, part_id)
        if version == 0:
            raise PartNotFoundException
        part_name = "%s%s%s" % (part_id, self.prefix, version)
        if not self.storeclient.exists(id, os.path.join(part_id, part_name)):
            raise VersionNotFoundException(part_id=part_id, version=version)
        else:
            return self.storeclient.get_stream(id, part_id, part_name, stream)

    def _del_part(self, id, part_id):
        if not self.storeclient.exists(id):
            raise ObjectNotFoundException
        if not self.storeclient.exists(id, part_id):
            raise PartNotFoundException(part_id=part_id)
        self.storeclient.del_path(id, part_id, recursive=True)
        if self.queue != None:
            self._log(id, 'd', 'Deleting a part', part_id=part_id)

    def _store_manifest(self, id, part_id, manifest, version = False):
        if not self.storeclient.exists(id):
            raise ObjectNotFoundException
        if not version:
            version = self._get_latest_part(id, part_id) + 1
        part_name = "%s%s%s" % (part_id, self.prefix, version)
        bytestream = manifest.to_string()
        if isinstance(bytestream, unicode):
            bytestream = bytestream.encode('utf-8')
        hexhash = self.storeclient.put_stream(id, part_id, part_name, bytestream)
        if self.queue != None:
            if version == 1:
                self._log(id, 'c', 'Creating an RDF Manifest', part_id=part_id, version=version, checksum=hexhash)
            else:
                self._log(id, 'w', 'Updating an RDF Manifest', part_id=part_id, version=version, checksum=hexhash)
        return {'version':version, 'checksum':hexhash}

    def _store_rdfobject(self, id, part_id, rdfobject, version=False):
        if not self.storeclient.exists(id):
            raise ObjectNotFoundException
        if not version:
            version = self._get_latest_part(id, part_id) + 1
        part_name = "%s%s%s" % (part_id, self.prefix, version)
        bytestream = rdfobject.to_string()
        if isinstance(bytestream, unicode):
            bytestream = bytestream.encode('utf-8')
        hexhash = self.storeclient.put_stream(id, part_id, part_name, bytestream)
        if self.queue != None:
            if version == 1:
                self._log(id, 'c', 'Creating an RDF Root', part_id=part_id, version=version, checksum=hexhash)
            else:
                self._log(id, 'w', 'Updating an RDF Root', part_id=part_id, version=version, checksum=hexhash)
        return {'version':version, 'checksum':hexhash}


    def _get_rdfobject(self, id, part_id, version = False):
        if not self.storeclient.exists(id):
            raise ObjectNotFoundException
        if not version:
            version = self._get_latest_part(id, part_id)
        part_name = "%s%s%s" % (part_id, self.prefix, version)
        r = RDFobject()
        r.set_uri(self.uri_base[id])
        if version >= 1:
            f = self.storeclient.get_stream(id, part_id, part_name,streamable=False)
            r.from_string(self.uri_base[id], f.decode('utf-8'))
        return r

    def _get_manifest(self, id, part_id, file_uri, version = False):
        if not self.storeclient.exists(id):
            raise ObjectNotFoundException
        if not version:
            version = self._get_latest_part(id, part_id)
        part_name = "%s%s%s" % (part_id, self.prefix, version)
        m = Manifest(file_uri)
        if version >= 1:
            f = self.storeclient.get_stream(id, part_id, part_name,streamable=False)
            m.from_string(f.decode('utf-8'))
        return m

    def exists(self, id):
        return self.storeclient.exists(id)

    def getObject(self, id=None, create_if_doesnt_exist=True):
        exists = self.storeclient.exists(id)
        self.storeclient.get_object(id, create_if_doesnt_exist)
        if create_if_doesnt_exist and not exists and self.queue != None:
            self._log(id, 'c', 'Creating an object')
        return FileStorageObject(id, self)

    def createObject(self, id):
        self.storeclient.create_object(id)
        if self.queue != None:
            self._log(id, 'c', 'Creating an object')
        return FileStorageObject(id, self)

    def deleteObject(self, id):
        if self.storeclient.exists(id):
            if self.queue != None:
                self._log(id, 'd', 'Deleting an object')
            return self.storeclient.delete_object(id)

    def log_audit(self, id, logcontext, context):
        if self.queue != None:
            self._log(id, 'metadatadelta', 'Metadata changes', _logcontext=logcontext, **context)

    def _log(self, id, action, label, **kw):
        msg = {}
        msg.update(kw)
        msg.update(self.context)
        msg['id'] = id
        msg['action'] = action
        msg['label'] = label
        msg['uri_base'] = self.uri_base
        # Get an ISO datetime for this
        msg['timestamp'] = datetime.now().isoformat()

        try:
            self.queue.put(simplejson.dumps(msg))
        except Exception, e:
            raise e
