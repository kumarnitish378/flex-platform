"""Converting between plain coordinates and PostGIS geography columns.

One place, because every module that stores a location needs the same two lines and the
lat/lng-versus-x/y order is exactly the kind of detail that gets flipped in a copy.
PostGIS points are (x, y) = (longitude, latitude); everything we speak is (lat, lng).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point as ShapelyPoint
from shapely.geometry import Polygon as ShapelyPolygon
from shapely.validation import explain_validity

from app.domain.errors import ValidationFailed


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


def to_polygon(ring: Sequence[tuple[float, float]]) -> Any:
    """A geography POLYGON from an outer ring of `(lat, lng)` pairs.

    Sent open or closed - the last point is joined to the first either way, because a
    map-drawing tool produces one and a GeoJSON export the other, and asking the caller
    to know which is a trap rather than a contract.

    Raises `ValidationFailed` for a ring that cannot be a zone: fewer than three
    distinct corners, or an outline that crosses itself. A self-intersecting ring is
    refused rather than repaired - `buffer(0)` would happily return one of the two
    lobes, and which one is a guess about what the operator meant.
    """
    points = [(lng, lat) for lat, lng in ring]
    if points and points[0] == points[-1]:
        points = points[:-1]
    if len(set(points)) < 3:
        raise ValidationFailed(
            "A zone needs at least three distinct corners", {"corners": len(set(points))}
        )

    polygon = ShapelyPolygon([*points, points[0]])
    if not polygon.is_valid:
        raise ValidationFailed("That outline crosses itself", {"reason": explain_validity(polygon)})
    return from_shape(polygon, srid=4326)


def ring(geography: Any) -> list[tuple[float, float]]:
    """`(lat, lng)` corners of a polygon read back out, closing point dropped."""
    shape = to_shape(geography)
    corners = list(shape.exterior.coords)
    if corners and corners[0] == corners[-1]:
        corners = corners[:-1]
    return [(lat, lng) for lng, lat in corners]
