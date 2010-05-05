from constructs import StoredEntity
from stores import FileStorageFactory, NotAPairtreeStoreException,  \
                   NotAValidStoreName, StoreAlreadyExistsException,  \
                   StoreNotFoundException

import os, shutil

import re

URI_BASE = "info:local/"
STORAGE_DIR = "./rdffilestore"
SPECIAL_FILE_PREFIX = "_"

class FileMultiEntityFactory(object):
    """Handles the connection to multiple, separate pairtree stores in the same root
    directory"""
    def _sanitise(self, name):
        p = re.compile(r'^[A-z][A-z0-9]*')
        m = p.match(name)
        if m:
            return m.group()
        else:
            raise NotAValidStoreName()

    def __init__(self, storage_dir='data', queue=None,
                        prefix=SPECIAL_FILE_PREFIX, shorty_length=2, hashing_type='md5'):
        self.stores = {}
        self.queue = queue
        self.storage_dir = storage_dir
        self.prefix = prefix
        self.shorty_length = shorty_length
        self.hashing_type = hashing_type
        self.status = self.init_stores()

    def __getitem__(self, index):
        return self.stores[index]
    def __setitem__(self, index, obj):
        self.stores[index] = obj
    def keys(self):
        return self.stores.keys()

    def __iter__(self):
        class Store_iter:
            def __init__(self, items, items_dict):
                self.items_dict = items_dict
                self.items = items
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
                    return (self.items[self.last-1], self.items_dict[self.items[self.last-1]])
        return Store_iter(self.stores.keys(), self.stores)

    def init_stores(self):
        status = {}
        if not os.path.exists(self.storage_dir):
            os.mkdir(self.storage_dir)
        else:
            for path in os.listdir(self.storage_dir):
                if os.path.isdir(os.path.join(self.storage_dir, path)):
                    try:
                        store_path = os.path.join(self.storage_dir, path)
                        store = FileEntityFactory(uri_base=None,
                                                  storage_dir=store_path,
                                                  queue=self.queue,
                                                  prefix=self.prefix,
                                                  shorty_length=self.shorty_length,
                                                  hashing_type=self.hashing_type)
                        status[path] = True
                        self.stores[path] = store
                    except NotAPairtreeStoreException,e :
                        # A rogue directory that isn't a pairtree store.
                        status[path] = False
        return status

    def get_store(self, store_name):
        store_name = self._sanitise(store_name)
        if store_name in self.stores:
            return self.stores[store_name]
        else:
            raise StoreNotFoundException

    def add_store(self, store_name, uri_base=None, queue=None, refresh=False):
        store_name = self._sanitise(store_name)
        if store_name in self.stores and not refresh:
            return self.stores[store_name]
        else:
            store_path = os.path.join(self.storage_dir, store_name)
            if self.queue  == None:
                store = FileEntityFactory(uri_base=uri_base,
                                    storage_dir=store_path,
                                    queue=queue,
                                    prefix=self.prefix,
                                    shorty_length=self.shorty_length)
            else:
                store = FileEntityFactory(uri_base=uri_base,
                                    storage_dir=store_path,
                                    queue=self.queue,
                                    prefix=self.prefix,
                                    shorty_length=self.shorty_length)
            self.status[store_name] = True
            self.stores[store_name] = store
            return store

    def delete_store(self, store_name):
        store_name = self._sanitise(store_name)
        store_path = os.path.join(self.storage_dir, store_name)
        if os.path.exists(store_path) and self.status[store_name] and os.path.isdir(store_path):
            shutil.rmtree(store_path)
            del self.status[store_name]
            del self.stores[store_name]

    def clone_store(self, copy_from_store, name_of_clone):
        store_name = self._sanitise(copy_from_store)
        name_of_clone = self._sanitise(name_of_clone)
        store_path = os.path.join(self.storage_dir, store_name)
        clone_path = os.path.join(self.storage_dir, name_of_clone)
        # Make sure store exists and is a store
        if os.path.exists(store_path) and self.status[store_name] and os.path.isdir(store_path):
            # Make sure clone store *doesn't* exist, and is not a store.
            if not (os.path.exists(clone_path) and self.status[name_of_clone] and os.path.isdir(clone_path)):
                shutil.copytree(store_path, clone_path)
                self.add_store(name_of_clone)
                return self.stores[name_of_clone]
            else:
                raise StoreAlreadyExistsException(clone_path)

    def rename_store(self, store_name, new_name):
        store_name = self._sanitise(store_name)
        new_name = self._sanitise(new_name)
        pass

    def list_ids(self, store):
        store = self._sanitise(store)
        if self.status.get(store, False) and store in self.stores:
            return self.stores[store].list_ids()

    def get(self, uri):
        pass

    def get_id(self, id, store):
        store = self._sanitise(store)
        if self.status.get(store, False) and store in self.stores:
            return self.stores[store].get_id(id)

class FileEntityFactory(object):
    def __init__(self, uri_base=URI_BASE, storage_dir=STORAGE_DIR,
                        queue=None, prefix=SPECIAL_FILE_PREFIX, shorty_length=2, 
                        hashing_type='md5', **context):
        """uri_base must end in an /, : or an #. If neither is present a / will be appended."""
        if uri_base and not(uri_base.endswith('/') or uri_base.endswith('#') or uri_base.endswith(':')):
            uri_base = "%s/" % uri_base
        factory_f = FileStorageFactory()
        self.hashing_type = hashing_type
        self._q = queue
        self._s = factory_f.get_store(uri_base, storage_dir, prefix, shorty_length, 
                                      queue, hashing_type=hashing_type, **context)
        self._c = context
        # The store might have a different idea on what the prefix is:
        self.uri_base = self._s.uri_base

    def exists(self, id):
        return self._s.exists(id)

    def get_id(self, id=None):
        uri = "%s%s" % (self.uri_base, id)
        s = StoredEntity(uri)
        s.init(id, self._s, **self._c)
        return s

    def get(self, uri):
        if uri.startswith(self.uri_base):
            id = uri[len(self.uri_base):]
            s = StoredEntity(uri)
            s.init(id, self._s, **self._c)
            return s
        else:
            raise Exception("TODO: uri not found")

    def delete(self, uri):
        if uri.startswith(self.uri_base):
            id = uri[len(self.uri_base):]
            return self.delete_id(id)
        else:
            raise Exception("TODO: uri not found")

    def delete_id(self, id):
        return self._s.deleteObject(id)

    def list_ids(self):
        """ EXPENSIVE - involves crawling the entire store pairtree directory"""
        return self._s.list_ids()

