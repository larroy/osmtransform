import constants
import math

def geo_dist(p0, p1):
    """Locally flat approximation"""
    avg_lat = (p0[1] + p1[1]) / 2.0
    avg_lon = (p0[0] + p1[0]) / 2.0
    parallel_of_latitude = constants.EARTH_CIRCUMFERENCE_X_M * math.cos(math.radians(avg_lat))
    meridian_of_longitude = constants.EARTH_CIRCUMFERENCE_Y_M
    delta_x = parallel_of_latitude * (p0[0] - p1[0]) / 360
    delta_y = meridian_of_longitude * (p0[1] - p1[1]) / 360
    return math.sqrt(delta_x ** 2 + delta_y ** 2)

def geo_dist_haversine(p0, p1):
    dlat = math.radians(p0[1] - p1[1])
    dlon = math.radians(p0[0] - p1[0])
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(p0[1]))\
        * math.cos(math.radians(p1[1])) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = constants.EARTH_RADIUS_M * c
    return d


