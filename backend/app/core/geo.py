"""Converting between plain coordinates and PostGIS geography columns.

One place, because every module that stores a location needs the same two lines and the
lat/lng-versus-x/y order is exactly the kind of detail that gets flipped in a copy.
PostGIS points are (x, y) = (longitude, latitude); everything we speak is (lat, lng).
"""

from __future__ import annotations

from typing import Any

from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point as ShapelyPoint


def to_point(lat: float, lng: float) -> Any:
    """A geography POINT for a column, from ordinary latitude and longitude."""
    return from_shape(ShapelyPoint(lng, lat), srid=4326)


def coords(geography: Any) -> tuple[float, float]:
    """`(lat, lng)` from a geography POINT read back out of the database.

    Typed loosely because SQLAlchemy hands back a `WKBElement` while the model column is
    annotated `object`; narrowing here would only move the cast somewhere less obvious.
    """
    shape = to_shape(geography)
    latitude: float = shape.y
    longitude: float = shape.x
    return latitude, longitude
