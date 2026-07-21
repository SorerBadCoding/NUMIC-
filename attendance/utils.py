from math import atan2, cos, radians, sin, sqrt

EARTH_RADIUS_METERS = 6371000


def haversine_distance_meters(lat1, lng1, lat2, lng2):
    phi1, phi2 = radians(lat1), radians(lat2)
    d_phi = radians(lat2 - lat1)
    d_lambda = radians(lng2 - lng1)
    a = sin(d_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(d_lambda / 2) ** 2
    return EARTH_RADIUS_METERS * 2 * atan2(sqrt(a), sqrt(1 - a))
