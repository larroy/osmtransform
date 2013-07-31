#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Transform raw osm data into objects"""

__author__ = 'Pedro Larroy'
__version__ = '0.1'

import os
import sys
import optparse
import logging
import optparse
from utils import pbar
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import pprint

sys.path.append('minimongo')
# load mongodb credentials
import minimongo
import mongocredentials
minimongo.configure(module = mongocredentials)

import planet
import osm
import datetime

def main():
    logging.basicConfig(level=logging.DEBUG)
    parser = optparse.OptionParser(usage = "%prog [options] [planet.area id]")
    (options, args) = parser.parse_args()
    if len(args) != 1:
        print "error: missing OSM dump file argument, run with --help option for help"
        return 1

    print 'Query', args[0]
    area_id = int(args[0])
    res = planet.Area.collection.find_one({"id": area_id })
    if not res:
        logging.error("Couldn't find a planet.area with id {0}".format(area_id))
        return 1

    pp = pprint.PrettyPrinter(indent=4)
    print 'Tags:'
    pp.pprint(res['tags'])
    print 'Way ids:'
    pp.pprint(res['memids'])

    #print res['tags']
    #print res['memids']
    #print len(res['outer'][0])
    #for a in planet.Area.collection.find():
    #    print a
    fig = plt.figure()
    ax = fig.add_subplot(111)

    (min_x, max_x) = (180, -180)
    (min_y, max_y) = (90, -90)
    for poly in res['outer']:
        ax.add_patch(patches.Polygon(poly, color='b', label='omg'))
        xs = [x[0] for x in poly]
        ys = [x[1] for x in poly]
        min_x = min(min_x, min(xs))
        max_x = max(max_x, max(xs))
        min_y = min(min_y, min(ys))
        max_y = max(max_y, max(ys))

    for poly in res['inner']:
        ax.add_patch(patches.Polygon(poly, color='#bbbbbb'))
        xs = [x[0] for x in poly]
        ys = [x[1] for x in poly]
        min_x = min(min_x, min(xs))
        max_x = max(max_x, max(xs))
        min_y = min(min_y, min(ys))
        max_y = max(max_y, max(ys))

    ax.set_xlim(min_x, max_x)
    ax.set_ylim(min_y, max_y)
    plt.show()



    return 0

if __name__ == '__main__':
    sys.exit(main())

