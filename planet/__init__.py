# -*- coding: utf-8 -*-

import minimongo
import osm
import pymongo.collection
import logging
import re
import stitch

def is_area(way):
    return len(way.nodes)\
        and way.nodes[0] == way.nodes[-1]\
        and ('area' in way.tags and way.tags['area'] == 'yes'\
            or (not 'highway' in way.tags\
                and not 'barrier' in way.tags))

def get_poly(nodes):
    """Get poly from a list of node ids"""
    poly = []
    for nodeid in nodes:
        for node in osm.Node.collection.find({"_id": nodeid}):
            poly.append((node.lon, node.lat))
    return poly

def truish(x):
    return x == "yes" or x == "true" or x == "1"

def falsish(x):
    return x == "no" or x == "false" or x == "0"

class Sink(object):
    def processWay(self, way):
        poly = get_poly(way.nodes)
        if is_area(way):
            if Area.connection.planet.multipolygon_ways.find({"_id": way._id}).count():
                #logging.debug("Skipping way %d as it belongs to a multipolygon relation", way._id)
                return

            parea = Area()
            parea.id = way._id
            parea.outer = poly
            parea.tags = way.tags
            parea.save()
        else:
            typ = Way.type_from_tags(way.tags)
            if not typ is None:
                pway = Way(way._id, poly, typ)
                pway.attr_from_tags(way.tags)
                pway.save()
            else:
                pline = Line(way._id, poly, way.tags)
                pline.save()

    def processNode(self, node):
        pass

    def processRelation(self, relation):
        typ = relation.tags.get('type', None)
        if typ == 'multipolygon':
            self.processRelationMultiPolygon(relation)

    def processRelationMultiPolygon(self, rel):
        """http://wiki.openstreetmap.org/wiki/Relation:multipolygon"""
        memids = []
        #logging.debug("%d members", len(rel.members))
        #logging.debug("relation %d", rel._id)
        #if len(rel.members)> 50:
        #    logging.debug('processRelationMultiPolygon: big rel')
        #    logging.debug("processing %d members", len(rel.members))
        #    logging.debug(rel._id)
        #    logging.debug(rel.tags)

        outer_stitch = stitch.Stitch(rel['_id'], True)
        inner_stitch = stitch.Stitch(rel['_id'], True)
        for m in rel.members:
            try:
                if m['type']  == 'way':
                    way = osm.Way.collection.find_one({"_id": m['ref']})
                    if way:
                        #logging.debug(way._id)
                        try:
                            if m['role'] == 'outer':
                                outer_stitch.add_id(get_poly(way.nodes), way._id)
                            elif m['role'] == 'inner':
                                inner_stitch.add_id(get_poly(way.nodes), way._id)
                        except RuntimeError,e:
                            print e, 'way id: ', way['_id'], 'relation id', rel['_id']
                        memids.append(way['_id'])
                        try:
                            Area.connection.planet.multipolygon_ways.insert({"_id": way._id}, safe=True)
                        except pymongo.errors.DuplicateKeyError:
                            pass
                    else:
                        logging.debug("cound't find way id: %d in multipolygon relation id %d", m['ref'], rel._id)
                        if m['role'] == 'outer':
                            outer_stitch.dontClose()
                        elif m['role'] == 'inner':
                            inner_stitch.autoClose()
            except KeyError:
                logging.warn("processRelationMultiPolygon: KeyError")
                return
        parea = Area()
        parea.id = rel._id
        try:
            parea.outer = outer_stitch.getPolygons()
        except RuntimeError, e:
            logging.warn("processRelationMultiPolygon exception: rel {0}: {1}".format(rel["_id"], e))
            logging.warn(memids)
        try:
            parea.inner = inner_stitch.getPolygons()
        except RuntimeError, e:
            logging.warn("processRelationMultiPolygon exception: rel {0}: {1}".format(rel["_id"], e))
            logging.warn(memids)
        parea.tags = rel.tags
        parea.memids = memids
        parea.save()
        #logging.debug("done")


    def processMember(self, member):
        pass


class Area(minimongo.Model):
    class Meta:
        database = 'planet'

#    def __init__(self, initial=None, **kw):
#        super(Area, self).__init__(initial, **kw)
#
#    def __init__(self, id, outer, inner, tags):
#        # might not be unique, can't use _id as we save areas from Ways and from Relations
#        self.id = id
#        self.outer = outer
#        self.inner = inner
#        self.tags = tags
#
class Line(minimongo.Model):
    class Meta:
        database = 'planet'

    def __init__(self, id, poly, tags):
        self._id = id
        self.poly = poly
        self.tags = tags

class Way(minimongo.Model):
    class Meta:
        database = 'planet'

    HW_MOTORWAY = 0
    HW_MOTORWAY_LINK = 1
    HW_TRUNK = 2
    HW_TRUNK_LINK = 3
    HW_PRIMARY = 4
    HW_PRIMARY_LINK = 5
    HW_SECONDARY = 6
    HW_SECONDARY_LINK = 7
    HW_TERTIARY = 8
    HW_TERTIARY_LINK = 9
    HW_LIVING_STREET = 10
    HW_PEDESTRIAN = 11
    HW_RESIDENTIAL = 12
    HW_UNCLASSIFIED = 13
    HW_SERVICE = 14
    HW_TRACK = 15
    HW_BUS_GUIDEWAY = 16
    HW_RACEWAY = 17
    HW_ROAD = 18
    HW_PATH = 19
    HW_FOOTWAY = 20
    HW_CYCLEWAY = 21
    HW_BRIDLEWAY = 22
    HW_STEPS = 23
    HW_PROPOSED = 24
    HW_CONSTRUCTION = 25

    def __init__(self, id, poly, typ):
        self._id = id
        self.poly = poly
        self.t = typ

    @staticmethod
    def type_from_tags(tags):
        if tags.has_key('highway'):
            try:
                val = tags['highway']
                attr = 'HW_{0}'.format(val.upper())
                hw = getattr(Way, attr)
                return hw
            except AttributeError:
                pass
            except UnicodeEncodeError:
                pass
        return None

    def attr_from_tags(self, tags):
        self.car_forward = True
        self.car_backward = True
        self.bike = True

        if tags.has_key('oneway'):
            ow = tags['oneway']
            if truish(ow):
                self.car_backward = False

            elif ow == "-1":
                self.car_backward = True

            #elif falsish(ow):
            #    pass

        if tags.has_key('roundabout'):
            self.roundabout = True
            if not tags.has_key('oneway'):
                self.car_backward = False

        if self.t == Way.HW_MOTORWAY or self.t == Way.HW_MOTORWAY_LINK and not tags.has_key('oneway'):
            self.car_forward = True
            self.car_backward = False

        if tags.has_key('maxspeed'):
            s = tags['maxspeed']
            m = re.match('\s*(\d+)\s*(\w*)\s*', s)
            if m:
                self.speedlimit = float(m.group(1))
                if m.group(2) == 'mph':
                    self.speedlimit *= 1.609344

        # TODO: no_thru
        if self.t >= Way.HW_PATH:
            self.car_forward = False
            self.car_backward = False

        # bikes
        if self.t <= Way.HW_MOTORWAY_LINK\
            or self.t == Way.HW_FOOTWAY\
            or self.t == Way.HW_STEPS:

            self.bike = False

        if truish(tags.get('bicycle', False)):
            self.bike = True



