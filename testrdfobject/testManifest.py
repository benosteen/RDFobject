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

from rdfobject.constructs import Manifest, ItemAlreadyExistsException, ItemDoesntExistException

m = Manifest()

RELSINT = """<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF
   xmlns:dataset="http://vocab.ouls.ox.ac.uk/dataset/scheme#"
   xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
>
  <rdf:Description rdf:about="info:fedora/uuid:8a360038-2282-11de-9609-000e2ed68b2b/TEXT_DESC">
    <dc:title>TEXT_DESC</dc:title>
    <dc:description>Data description</dc:description>
  </rdf:Description>
  <rdf:Description rdf:about="info:fedora/uuid:23e0e1ca-2284-11de-9609-000e2ed68b2b/raw.wav">
    <dc:title>raw.wav</dc:title>

    <dc:description>the original recording, in Microsoft WAV format.
It is a two-channel file.  One channel contains the
recorded speech, and the other channel contains either
metronome ticks or an audio channel from a microphone
positioned to pick up finger taps.   (The subject's finger
tapped on a hardcover book about 2cm from the microphone.)
The finger tap channel will pick up some speech, but faintly,
and the speech channel will pick up some finger tap sounds.
However, metronome ticks were coupled in electronically and
are completely isolated from the speech channel.</dc:description>
    <dataset:physicalPath>/jf/jf_rep3_tap/raw.wav</dataset:physicalPath>
  </rdf:Description>
  <rdf:Description rdf:about="info:fedora/uuid:23e0e1ca-2284-11de-9609-000e2ed68b2b/loud.dat">
    <dc:title>loud.dat</dc:title>
    <dc:description>The perceptual loudness.</dc:description>
    <dataset:physicalPath>/jf/jf_rep3_tap/loud.dat</dataset:physicalPath>

  </rdf:Description>
  <rdf:Description rdf:about="info:fedora/uuid:23e0e1ca-2284-11de-9609-000e2ed68b2b/pdur.dat">
    <dc:title>pdur.dat</dc:title>
    <dc:description>A measure of duration for the current syllable.
Essentially, it measures how far one can go (in time)
before the spectrum changes substantially.</dc:description>
    <dataset:physicalPath>/jf/jf_rep3_tap/pdur.dat</dataset:physicalPath>
  </rdf:Description>
  <rdf:Description rdf:about="info:fedora/uuid:23e0e1ca-2284-11de-9609-000e2ed68b2b/raw.ue">

    <dc:title>raw.ue</dc:title>
    <dc:description></dc:description>
    <dataset:physicalPath>/jf/jf_rep3_tap/raw.ue</dataset:physicalPath>
  </rdf:Description>
  <rdf:Description rdf:about="info:fedora/uuid:23e0e1ca-2284-11de-9609-000e2ed68b2b/aggregation">
    <dc:title>Aggregation</dc:title>
    <rdf:type rdf:resource="http://example.org"/>
  </rdf:Description>
  <rdf:Description rdf:about="info:fedora/uuid:23e0e1ca-2284-11de-9609-000e2ed68b2b/ue.lbl">
    <dc:title>ue.lbl</dc:title>
    <dc:description>These are the start and end-points of the speech in the
utterance, automatically generated but checked for accuracy
by a human.   A small amount of silence (probably &lt;100ms)
is included within
the marked endpoints on either side of the utterance.</dc:description>

    <dataset:physicalPath>/jf/jf_rep3_tap/ue.lbl</dataset:physicalPath>
  </rdf:Description>
  <rdf:Description rdf:about="info:fedora/uuid:23e0e1ca-2284-11de-9609-000e2ed68b2b/f0.dat">
    <dc:title>f0.dat</dc:title>
    <dc:description>A standard computation of the speech fundamental frequency.</dc:description>
    <dataset:physicalPath>/jf/jf_rep3_tap/f0.dat</dataset:physicalPath>
  </rdf:Description>

  <rdf:Description rdf:about="info:fedora/uuid:23e0e1ca-2284-11de-9609-000e2ed68b2b/raw.tap">
    <dc:title>raw.tap</dc:title>
    <dc:description>This file contains experimental tick or tap events.
For the metronome data, it contains the times at which
metronome ticks occur.   For the "tick" data, if it
exists, it lists the times at which the subject's finger
tapped to mark a stressed syllable.
This is computed from one of the channels of the raw.wav file,
but manually checked.</dc:description>
    <dataset:physicalPath>/jf/jf_rep3_tap/raw.tap</dataset:physicalPath>
  </rdf:Description>
  <rdf:Description rdf:about="info:fedora/uuid:23e0e1ca-2284-11de-9609-000e2ed68b2b/irr.dat">
    <dc:title>irr.dat</dc:title>

    <dc:description>An irregularity measure that separates voiced speech
from unvoiced.   It quantifies speech that is not fully voiced.</dc:description>
    <dataset:physicalPath>/jf/jf_rep3_tap/irr.dat</dataset:physicalPath>
  </rdf:Description>
  <rdf:Description rdf:about="info:fedora/uuid:23e0e1ca-2284-11de-9609-000e2ed68b2b/tap.dat">
    <dc:title>tap.dat</dc:title>
    <dc:description></dc:description>
    <dataset:physicalPath>/jf/jf_rep3_tap/tap.dat</dataset:physicalPath>

  </rdf:Description>
  <rdf:Description rdf:about="info:fedora/uuid:23e0e1ca-2284-11de-9609-000e2ed68b2b/rms.dat">
    <dc:title>rms.dat</dc:title>
    <dc:description>The RMS (intensity or power).</dc:description>
    <dataset:physicalPath>/jf/jf_rep3_tap/rms.dat</dataset:physicalPath>
  </rdf:Description>
  <rdf:Description rdf:about="info:fedora/uuid:23e0e1ca-2284-11de-9609-000e2ed68b2b/sss.dat">

    <dc:title>sss.dat</dc:title>
    <dc:description>A measurement of the average slope of the speech spectrum.</dc:description>
    <dataset:physicalPath>/jf/jf_rep3_tap/sss.dat</dataset:physicalPath>
  </rdf:Description>
</rdf:RDF>
"""

m.from_string(RELSINT)

print m.to_string(format="n3")

print "-="*20

# Manifest works like an iterator, yielding RDFobjects in the order given in 
# its internal Manifest.items list. The list can be reordered via sort() or similar

for item in m:
    if item.types:
        print 'Typed object: %s -> %s' % (item.types, item.uri)
        # Adding a bit of info about this item (note, simply adding to m, not the item directly)
        m.add_triple(item.uri, "dc:description", 
                "This is an example.org object, totally pointless, but that's how it goes")
        m.add_triple(item.uri, "dc:format", "text/xml")
        print "-="*20
        print "Print this now adjusted item as ntriples\n"
        print item.to_string(format="nt")
        print "-="*20
    else:
        print "Untyped object, likely a file: %s" % (item.uri)

# Creating new items

item_id = u"info:fedora/uuid:23e0e1ca-2284-11de-9609-000e2ed68b2b/the_shizzle.txt"

print "Creating item %s explicitly" % (item_id)

m.add_item(item_id)

m.add_triple(item_id, "dc:format", "text/plain")

print "Attempting to create the item again erroneously"

try:
    m.add_item(item_id)
except ItemAlreadyExistsException:
    print "Item not overwritten accidentally"

print "Getting the item's RDFobject"

fragment = m.get_item(item_id)
print "-="*20
print "What is fragment (should be an RDFobject) \n%s\n\n" % (type(fragment))

print fragment.to_string()
print "-="*20

print "Now just adding the triples - new items will be created automagically"

# or just add the triples - new items will be created automagically
item_id2 = u"info:fedora/externalitem:1/magic.jpg"

m.add_triple(item_id2, "dc:format", "image/jpg")
m.add_triple(item_id2, "dc:title", "It's magic")

print "Getting the magically created item's RDFobject"

fragment = m.get_item(item_id2)
print "-="*20

print fragment.to_string()

print "-="*20
print "The final, full manifest object"
print m.to_string(format="n3")
