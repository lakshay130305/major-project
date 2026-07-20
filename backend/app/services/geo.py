"""Geospatial helpers: haversine distance, point-in-polygon, route deviation."""
import json
import math

from shapely.geometry import Point, Polygon

from app.models.zone import Zone

EARTH_RADIUS_M = 6_371_000.0


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two lat/lng points, in metres."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def point_in_zone(lat: float, lng: float, zone: Zone) -> bool:
    """Point-in-polygon test using shapely. Polygon is stored as [[lat,lng],...]."""
    verts = json.loads(zone.polygon)
    if len(verts) < 3:
        return False
    # shapely uses (x=lng, y=lat)
    poly = Polygon([(v[1], v[0]) for v in verts])
    return poly.contains(Point(lng, lat))


def zones_containing_point(lat: float, lng: float, zones: list[Zone]) -> list[Zone]:
    return [z for z in zones if point_in_zone(lat, lng, z)]


def min_distance_to_route(lat: float, lng: float, itinerary: list[dict]) -> float:
    """Minimum distance (m) from a point to any planned itinerary waypoint.

    A simple, explainable proxy for route-deviation: if the tourist strays
    further than a threshold from every planned stop, they've deviated.
    """
    if not itinerary:
        return 0.0
    return min(haversine_m(lat, lng, wp["lat"], wp["lng"]) for wp in itinerary)
