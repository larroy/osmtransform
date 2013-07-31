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
import matplotlib.lines as lines
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
    parser = optparse.OptionParser(usage = "%prog [options] [osm.way _id]")
    (options, args) = parser.parse_args()
    if len(args) != 1:
        print "error: specify osm.relation _id as argument"
        return 1

    print 'Query', args[0]
    pp = pprint.PrettyPrinter(indent=4)

    rel_id = int(args[0])

    rel = osm.Relation.collection.find_one({"_id": rel_id})
    if not rel:
        sys.stderr.write("Relation not found")
        return 1

    ways = []
    for m in rel.members:
        if m['type']  == 'way':
            way = osm.Way.collection.find_one({"_id": m['ref']})
            if not way:
                logging.error("Couldn't find a way with id {0}".format(m['ref']))
            else:
                print "id:", way["_id"]
                print 'Tags:'
                pp.pprint(way['tags'])

                if m['role'] == 'outer':
                    way.role = 'outer'
                elif m['role'] == 'inner':
                    way.role = 'inner'
                else:
                    continue
                ways.append(way)


    fig = plt.figure()
    ax = fig.add_subplot(111)

    (min_x, max_x) = (180, -180)
    (min_y, max_y) = (90, -90)
    for way in ways:
        poly = planet.get_poly(way.nodes)
        print poly
        xs = [x[0] for x in poly]
        ys = [x[1] for x in poly]
        if way.role == 'outer':
            ax.add_line(lines.Line2D(xs, ys, color='b', label='omg'))
        else:
            ax.add_line(lines.Line2D(xs, ys, color='r', label='omg'))
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

