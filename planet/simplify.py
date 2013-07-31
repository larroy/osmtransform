

#
# To simplify in geographic coordinates (lat, lon) we create a graticule on the
# earth sphere with the appropiate angle at each level. Taking into account the
# scale factor of the mercator projection for example, it would be a need for a
# safety margin (eg. 5x) so simplification is not too agressive at higher
# latitudes due to the vertical distortion.
#
import bisect
import math

def clamp(intervals, x):
    """
    Clamp the value of x in the range [intervals[0], intervals[-1]) to the values of the interval list
    >>> clamp([1,2,3],0.9)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "simplify.py", line 18, in clamp
        raise ValueError
    ValueError
    >>> clamp([1,2,3], 3)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "simplify.py", line 27, in clamp
        raise ValueError
    ValueError
    >>> clamp([1,2,3], 2.1)
    2
    """
    i = bisect.bisect_right(intervals, x)
    if i and i != len(intervals):
        return intervals[i-1] + (intervals[i] - intervals[i-1]) / 2
    else:
        raise ValueError

def drange(start, stop, step):
    r = start
    while r < stop:
            yield r
            r += step

class HGrat(object):
    """Horizontal Graticule
    >>> g = HGrat(0.1)
    >>> g[0]
    -180.0
    >>> len(g)
    3600
    >>> g[2]
    -179.8
    """
    def __init__(self, step):
        self.step = step
        self.start = -180
        self.stop = 180
        self.len = int(math.floor(abs(self.stop - self.start) / self.step))

    def __len__(self):
        return self.len

    def __getitem__(self, key):
        if key >= 0 and key < self.len:
            res = self.start + key * self.step
            assert(res <= self.stop)
            return res
        else:
            raise IndexError

class VGrat(object):
    """Vertical Graticule
    """
    def __init__(self, step):
        self.step = step
        self.start = -85
        self.stop = 85
        self.len = int(math.floor(abs(self.stop - self.start) / self.step))

    def __len__(self):
        return self.len

    def __getitem__(self, key):
        if key >= 0 and key < self.len:
            res = self.start + key * self.step
            assert(res <= self.stop)
            return res
        else:
            raise IndexError

def deg2m(x):
    return (40000000/360)*x

class Simplify(object):
    NPIXELS = 256
    NZLEVELS = 18
    # 5 for mercator distortion times 2 for half pixel resolution
    RES_FACTOR = 10

    # Fill the graticule given the inverse mercator projection of it
    # Allowed range is [0, len)
    LAT_GRATICULE = []
    LON_GRATICULE = []

    # Coarseness of the graticule for a given zoom level in projected coordinates
    # To be accurate, the grid should vary with longitude with the sec function
    # given the vertical distortion. For now we make it constant.
    STEP_LEVEL = list()
    for lvl in range(NZLEVELS):
        STEP_LEVEL.append(360.0 / (NPIXELS * RES_FACTOR * (1 << lvl)))
        print "lvl: {0} {1:0.3e} degrees {2:0.3f} m".format(lvl, STEP_LEVEL[-1], deg2m(STEP_LEVEL[-1]))
        LAT_GRATICULE.append(HGrat(STEP_LEVEL[-1]))
        LON_GRATICULE.append(VGrat(STEP_LEVEL[-1]))


    #assert(len(LAT_GRATICULE) > 2)
    #assert(len(LON_GRATICULE) > 2)

    @staticmethod
    def simplify(lat, lon, level):
        '''Simplify geometry in geospatial coordinates given zoom level :param level
        raises ValueError when the passed coordinates are out of the allowed ranges above or below
        '''
        return (clamp(Simplify.LAT_GRATICULE[level], lat), clamp(Simplify.LON_GRATICULE[level], lon))


