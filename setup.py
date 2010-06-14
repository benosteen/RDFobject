from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages

setup(name="RDFobject",
      version="0.4.1",
      description="RDFobject - classes for dealing with entities and things in RDF",
      long_description="""\
RDFobject - a set of python classes to make it easy to deal with RDF concerning entities or things.
Has the ability to store objects to a filesystem using the pairtree specification, and adopts the
fedora-commons model that objects have attached 'parts' - files, metadata, etc.
""",
      author="Ben O'Steen",
      author_email="bosteen@gmail.com",
      packages=find_packages(exclude='tests'),
      install_requires=['rdflib>=2.4.2', 'simplejson', 'httplib2==0.5.0', 'pairtree>=0.4'],
      )

