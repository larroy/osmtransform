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
    if len(args) < 1:
        print "error: specify osm.way _id as argument"
        return 1

    print 'Query', args[0]
    pp = pprint.PrettyPrinter(indent=4)

    way_ids = map(lambda x: int(x), args)
    ways = []
    for wid in way_ids:
        res = osm.Way.collection.find_one({"_id": wid })
        if not res:
            logging.error("Couldn't find a way with id {0}".format(way_id))
        else:
            print 'Tags:'
            pp.pprint(res['tags'])
            ways.append(res)


    fig = plt.figure()
    ax = fig.add_subplot(111)

    (min_x, max_x) = (180, -180)
    (min_y, max_y) = (90, -90)
    for way in ways:
        poly = planet.get_poly(way.nodes)
        xs = [x[0] for x in poly]
        ys = [x[1] for x in poly]
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

