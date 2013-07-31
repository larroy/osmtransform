import logging
import unittest
import collections
import copy
import pdb
import functools
import utils

def other_way(way, ways):
    for w in ways:
        if w != way:
            return w
    return None


def other_point(way, point):
    if point == way[0]:
        return way[-1]
    elif point == way[-1]:
        return way[0]
    else:
        raise RuntimeError("other_point: the point is not an endpoint: point {0} way {1}".format(way, point))

def walk(way, point):
    """Return the points in way in the direction from point"""
    if point == way[0]:
        return way
    elif point == way[-1]:
        res = copy.deepcopy(way)
        res.reverse()
        return res
    else:
        raise RuntimeError("walk: the point is not an endpoint")

class Stitch(object):
    def __init__(self, relid = None, heuristic_closing = False):
        # Hash of way endpoints to connect the polygons
        self.endpoint = collections.defaultdict(list)
        # All the assembled polygons
        self.polygons = list()
        # The ones we have gone through when processing
        self.seen = dict()
        self.id = collections.defaultdict(list)
        self.heuristic_closing = heuristic_closing
        self.relid = relid

    def add_id(self, inpoly, id):
        self.id[inpoly[0]].append(id)
        self.id[inpoly[-1]].append(id)
        self.add(inpoly)

    def dontClose(self):
        self.heuristic_closing = False

    def autoClose(self):
        self.heuristic_closing = True

    def add(self, inpoly):
        poly = inpoly
        # already closed
        if len(poly) < 2:
            logging.warn("stitch.Stitch.add: way with < 2 vertices")
            return
        if poly[0] == poly[-1]:
            self.polygons.append(poly)
        else:
            self.endpoint[poly[0]].append(poly)
            if len(self.endpoint[poly[0]]) > 2:
                raise RuntimeError("more than two ways with common endpoint point ({0}) on a multipolygon relation are invalid, ids: {1}".format(poly[0], self.id.get(poly[0])))

            self.endpoint[poly[-1]].append(poly)
            if len(self.endpoint[poly[-1]]) > 2:
                raise RuntimeError("more than two ways with common endpoint point ({0}) on a multipolygon relation are invalid, ids: {1}".format(poly[-1], self.id.get(poly[-1])))

    def jump_nearest(self, cur_point, cur_way):
        """Jump to closest open endpoint"""
        dest = None
        candidates = []
        for p in self.endpoint.keys():
            if p not in self.seen and cur_way not in self.endpoint[p] and len(self.endpoint[p]) == 1:
                candidates.append(p)
        if candidates:
            dist_cur = functools.partial(utils.geo_dist, cur_point)
            dest = min(candidates, key = dist_cur)
        way = None
        if dest:
            way = self.endpoint[dest][0]
        return (dest, way)

    def next_junction(self):
        for p in self.endpoint.keys():
            if p not in self.seen and len(self.endpoint[p]) > 1:
                yield p

    def getPolygons(self):
        """Assemble polygons out of the chunks encoded in ways"""
        for first_point in self.next_junction():
            polygon = []
            first_way = self.endpoint[first_point][0]
            cur_way = first_way
            cur_point = first_point
            while True:
                self.seen[cur_point] = True
                duplicated_endpoint = None
                if polygon:
                    duplicated_endpoint = polygon.pop() # first point is the last previous point, remove
                polygon.extend(walk(cur_way, cur_point))
                cur_point = other_point(cur_way, cur_point)
                cur_way = other_way(cur_way, self.endpoint[cur_point])
                if not cur_way:
                    # this is a dead end
                    self.seen[cur_point] = True
                    cur_way = self.endpoint[cur_point][0]
                    if self.heuristic_closing:
                        assert(polygon)
                        # reintroduce the last endpoint
                        polygon.append(duplicated_endpoint)
                        (cur_point, cur_way) = self.jump_nearest(cur_point, cur_way)
                        if not cur_point or not cur_way:
                            logging.warn("stitch.Stitch.getPolygons: polygon in rel {0} is unclosed at {1}, unable to close".format(self.relid, cur_point))
                            break
                        logging.warn("stitch.Stitch.getPolygons: polygon in rel {0} is unclosed at {1}, heuristically closed".format(self.relid, cur_point))
                    else:
                        logging.warn("stitch.Stitch.getPolygons: polygon in rel {0} is unclosed at {1}".format(self.relid, cur_point))
                        break

                #pdb.set_trace()
                #if cur_way == first_way or self.endpoint == self.seen:
                if cur_way == first_way:
                    assert(cur_point == first_point)
                    if polygon[0] == polygon[-1]:
                        self.polygons.append(polygon)
                    else:
                        logging.warn("stitch.Stitch.getPolygons: Unclosed polygon in rel {0}".format(self.relid))
                        logging.debug(polygon)
                    break

                if self.seen.get(cur_point):
                    #logging.debug("stitch.Stitch.getPolygons: found a traversed path".format(self.relid, cur_point))
                    break

        return self.polygons


def equiv(xs, ys):
    if len(xs) != len(ys):
        return False
    for (i, x) in enumerate(xs):
        y = ys[i]
        if len(x) != len(y):
            return False
        elif x == y:
            continue
        else:
            rotation = False
            x_ = x[:-1]
            for rot_n in range(len(x_)):
                rot = collections.deque(x_)
                rot.rotate(rot_n)
                rot_x = list(rot)
                rot_x.append(rot_x[0])
                if rot_x == y:
                    rotation = True
                    break
            x_.reverse()
            for rot_n in range(len(x_)):
                rot = collections.deque(x_)
                rot.rotate(rot_n)
                rot_x = list(rot)
                rot_x.append(rot_x[0])
                if rot_x == y:
                    rotation = True
                    break

            if not rotation:
                return False

    return True

class StitchTest(unittest.TestCase):
    def test_equiv(self):
        self.assertTrue(equiv([[1,2,4,1]],[[1,2,4,1]]))
        self.assertTrue(equiv([[1,2,4,1]],[[2,4,1,2]]))
        self.assertFalse(equiv([[1,2,4,1]],[[2,4,4,2]]))
        self.assertTrue(equiv([[1,2,4,1]],[[4,2,1,4]]))

    def test_0(self):
        return
        s = Stitch()
        s.add([(0,0), (2,2), (2,0), (0,0)])
        self.assertEqual(s.getPolygons(), [
            [(0,0), (2,2), (2,0), (0,0)]
        ])

    def test_1(self):
        s = Stitch()
        s.add([(0,0), (2,2), (2,0)])
        s.add([(2,0), (1,0)])
        s.add([(1,0), (0,0)])

        s.add([(4,0), (6,2), (6,0)])
        s.add([(6,0), (5,0)])
        s.add([(5,0), (4,0)])
        expect =  [
            [(0,0), (2,2), (2,0), (1,0), (0,0)],
            [(4,0), (6,2), (6,0), (5,0), (4,0)]
        ]
        #print expect
        #print s.getPolygons()
        self.assertTrue(equiv(s.getPolygons(), expect))

    def test_2(self):
        s = Stitch()
        s.add([(0,0), (2,2), (2,0)])
        s.add([(1,0), (2,0)]) # flipped
        s.add([(1,0), (0,0)])

        s.add([(4,0), (6,2), (6,0)])
        s.add([(6,0), (5,0)])
        s.add([(4,0), (5,0)]) # flipped

        expect =  [
            [(0,0), (2,2), (2,0), (1,0), (0,0)],
            [(4,0), (6,2), (6,0), (5,0), (4,0)]
        ]

        self.assertTrue(equiv(s.getPolygons(), expect))

    def test_3(self):
        #logging.basicConfig(level=logging.CRITICAL)
        s = Stitch()
        s.add([(3,3), (3,4), (3,5), (3,3)])
        s.add([(0,0), (2,2), (2,0)])
        s.add([])
        s.getPolygons()

    def test_4(self):
        #logging.basicConfig(level=logging.DEBUG)
        s = Stitch()
        s.add([(3,3), (3,4), (3,5)])
        s.add([(0,0), (2,2), (2,0)])
        s.add([(0,0), (2,2), (2,0), (3,5)])
        s.getPolygons()

    def test_4(self):
        """Close two polygons heuristically"""
        s = Stitch()
        s.autoClose()
        s.add([(0,0), (1,0)])
        s.add([(2,0), (3,0), (4,0), (4,1), (3,1), (0,0)])
        expect =  [
            [(0,0), (1,0), (2,0), (3,0), (4,0), (4,1), (3,1), (0,0)]
        ]
        #print s.getPolygons()
        #print expect
        #print s.getPolygons() == expect
        self.assertTrue(equiv(s.getPolygons(), expect))



