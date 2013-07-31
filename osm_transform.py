#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Transform raw osm data into objects"""

__author__ = 'Pedro Larroy'
__version__ = '0.1'

import os
import sys
import optparse
import logging
from utils import pbar

sys.path.append('minimongo')
# load mongodb credentials
import minimongo
import mongocredentials
minimongo.configure(module = mongocredentials)

import planet
import osm
import datetime

def processRelations(sink):
    from planet import Area
    Area.connection.planet.multipolygon_ways.drop()
    total = osm.Relation.collection.count()
    progress = pbar.ProgressBar(0, total)
    print 'Processing relations:'
    i = 0
    start = datetime.datetime.now()
    for r in osm.Relation.collection.find(timeout = False):
        if i % 10 == 0:
            msg = '{0}/{1} '.format(i, total) + pbar.est_finish(start, i, total)
            progress(i, msg)
        sink.processRelation(r)
        i += 1
    progress(i)
    print

def processWays(sink):
    total = osm.Way.collection.count()
    progress = pbar.ProgressBar(0, total)
    print 'Processing Ways:'
    i = 0
    start = datetime.datetime.now()
    for r in osm.Way.collection.find(timeout = False):
        if i % 100 == 0:
            msg = '{0}/{1} '.format(i, total) + pbar.est_finish(start, i, total)
            progress(i, msg)
        sink.processWay(r)
        i += 1
    progress(i)
    print



def main():
    sink = planet.Sink()
    logging.basicConfig(level=logging.DEBUG)
    processRelations(sink)
    #processWays(sink)
    return 0

if __name__ == '__main__':
    sys.exit(main())

