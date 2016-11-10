import math

from django.contrib.gis.gdal import CoordTransform
from django.contrib.gis.gdal import SpatialReference
from django.contrib.gis.geos import MultiPolygon
from django.contrib.gis.geos import Polygon
from django.contrib.gis.measure import Distance


def bounding_box_to_polygon(bbox):
    min_x, min_y, max_x, max_y = tuple(bbox)
    points = (min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y), (min_x, min_y)
    return Polygon(points)


def compass_bearing(pointA, pointB):
    """
    Calculates the bearing between two points.
    The formulae used is the following:
        θ = atan2(sin(Δlong).cos(lat2),
                  cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(Δlong))
    :Parameters:
      - `pointA: The tuple representing the latitude/longitude for the
        first point. Latitude and longitude must be in decimal degrees
      - `pointB: The tuple representing the latitude/longitude for the
        second point. Latitude and longitude must be in decimal degrees
    :Returns:
      The bearing in degrees
    :Returns Type:
      float
    """

    lat1 = math.radians(pointA.y)
    lat2 = math.radians(pointB.y)

    diffLong = math.radians(pointB.x - pointA.x)

    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
                                           * math.cos(lat2) * math.cos(diffLong))

    initial_bearing = math.atan2(x, y)

    # Now we have the initial bearing but math.atan2 return values
    # from -180° to + 180° which is not what we want for a compass bearing
    # The solution is to normalize the initial bearing as shown below
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing


PROJ_7314 = SpatialReference(
    'PROJCS["NA Lambert Azimuthal Equal Area",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["degree",0.0174532925199433]],PROJECTION["Lambert_Azimuthal_Equal_Area"],PARAMETER["false_easting",0.0],PARAMETER["false_northing",0.0],PARAMETER["longitude_of_center",-100.0],PARAMETER["latitude_of_center",45.0],UNIT["meter",1.0]]')
PROJ_4326 = SpatialReference('EPSG:4326')

PROJ_4326_TO_7314 = CoordTransform(PROJ_4326, PROJ_7314)
PROJ_7314_TO_4326 = CoordTransform(PROJ_7314, PROJ_4326)


def unwrap_polygon(polygon):
    """
    Given a polygon, returns a corresponding polygon that 'unwraps' the coordinate such, if the
    coordinates cross the anti-meridian, the longitudes are changed to be only positive or negative.

    This fixes weird issues that may occur at the anti-meridian,
    so that a polygon is now represented as (160 45), (200 45), (200, 55), (160, 55), (160 45)
    instead of (160 45), (-160 45), (-160, 55), (160, 55), (160 45)

    This function assumes that we always want to wrap the polygon around the world the shortest
    possible way, defaulting to wrapping around the prime meridian if the polygon wraps around
    exactly half of the globe
    """
    # Get all the longitudes from the passed-in coordinates
    longitudes = [c[0] for c in polygon.coords[0]]
    # If the sum total of the minimum and maximum longitudes is greater than 180, we're wrapping
    # around the anti-meridian; otherwise, we can just leave the polygon alone (if it happens to be
    # *exactly* halfway around the globe, we default to wrapping around the *prime* meridian)
    if (abs(min(longitudes)) + abs(max(longitudes))) <= 180:
        return polygon

    # We have to figure out if the resulting longitude should be positive or negative; we decide
    # that based on which side of the polygon is "larger" (has the smallest longitude) after
    # splitting it on the anti-meridian
    smallest_longitude = min(longitudes, key=lambda value: abs(value))

    # Use that point to determine what sign we use for longitudes
    is_negative_lng = True if smallest_longitude < 0 else False
    unwrapped_coords = []

    for point in polygon.coords[0]:
        lng = point[0]
        lat = point[1]

        if is_negative_lng and lng > 0:
            unwrapped_coords.append((lng - 360, lat))
        elif not is_negative_lng and lng < 0:
            unwrapped_coords.append((lng + 360, lat))
        else:
            unwrapped_coords.append(point)

    return Polygon(unwrapped_coords)


def unwrap_multipolygon(multipolygon):
    """
    Given a multipolygon, returns a corresponding multipolygon with the
    coordinates of each of the contained polygons 'unwrapped'
    """
    for i in range(0, len(multipolygon)):
        multipolygon[i] = unwrap_polygon(multipolygon[i])
    return multipolygon


def buffer_geometry(geometry, extent_in_nm):
    """
    Buffer geometry by projecting it to a coordinate system
    in meters.

    Buffer the geometry by extent_in_nm.

    Reproject the geometry back into WGS84
    """
    extent_in_m = Distance(nm=extent_in_nm).m
    projected = geometry.transform(PROJ_4326_TO_7314, clone=True)
    buffered = projected.buffer(extent_in_m)
    buffered.srid = 7314
    unprojected = buffered.transform(PROJ_7314_TO_4326, clone=True)
    unprojected.srid = 4326
    multipolygon = unwrap_multipolygon(MultiPolygon(unprojected))
    multipolygon.srid = 4326
    return multipolygon


def build_circle(point, extent_in_nm):
    """
    Build a buffered polygon that is the correct distance
    around the point.
    """
    point.srid = 4326
    return buffer_geometry(point, extent_in_nm)
