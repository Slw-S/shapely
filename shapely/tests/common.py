import sys
from contextlib import contextmanager

import numpy as np
import pytest

import shapely

shapely20_todo = pytest.mark.xfail(strict=False, reason="Not yet implemented for Shapely 2.0")

point_polygon_testdata = (
    shapely.points(np.arange(6), np.arange(6)),
    shapely.box(2, 2, 4, 4),
)
point = shapely.points(2, 3)
line_string = shapely.linestrings([(0, 0), (1, 0), (1, 1)])
linear_ring = shapely.linearrings([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
polygon = shapely.polygons([(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)])
multi_point = shapely.multipoints([(0, 0), (1, 2)])
multi_line_string = shapely.multilinestrings([[(0, 0), (1, 2)]])
multi_polygon = shapely.multipolygons(
    [
        [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)],
        [(2.1, 2.1), (2.2, 2.1), (2.2, 2.2), (2.1, 2.2), (2.1, 2.1)],
    ]
)
geometry_collection = shapely.geometrycollections(
    [shapely.points(51, -1), shapely.linestrings([(52, -1), (49, 2)])]
)
point_z = shapely.points(2, 3, 4)
line_string_z = shapely.linestrings([(0, 0, 4), (1, 0, 4), (1, 1, 4)])
polygon_z = shapely.polygons([(0, 0, 4), (2, 0, 4), (2, 2, 4), (0, 2, 4), (0, 0, 4)])
geometry_collection_z = shapely.geometrycollections([point_z, line_string_z])
polygon_with_hole = shapely.Geometry(
    "POLYGON((0 0, 0 10, 10 10, 10 0, 0 0), (2 2, 2 4, 4 4, 4 2, 2 2))"
)
empty_point = shapely.Geometry("POINT EMPTY")
empty_point_z = shapely.Geometry("POINT Z EMPTY")
empty_line_string = shapely.Geometry("LINESTRING EMPTY")
empty_line_string_z = shapely.Geometry("LINESTRING Z EMPTY")
empty_polygon = shapely.Geometry("POLYGON EMPTY")
empty = shapely.Geometry("GEOMETRYCOLLECTION EMPTY")
line_string_nan = shapely.linestrings([(np.nan, np.nan), (np.nan, np.nan)])
multi_point_z = shapely.multipoints([(0, 0, 4), (1, 2, 4)])
multi_line_string_z = shapely.multilinestrings([[(0, 0, 4), (1, 2, 4)]])
multi_polygon_z = shapely.multipolygons(
    [
        [(0, 0, 4), (1, 0, 4), (1, 1, 4), (0, 1, 4), (0, 0, 4)],
        [(2.1, 2.1, 4), (2.2, 2.1, 4), (2.2, 2.2, 4), (2.1, 2.2, 4), (2.1, 2.1, 4)],
    ]
)
polygon_with_hole_z = shapely.Geometry(
    "POLYGON Z((0 0 4, 0 10 4, 10 10 4, 10 0 4, 0 0 4), (2 2 4, 2 4 4, 4 4 4, 4 2 4, 2 2 4))"
)

all_types = (
    point,
    line_string,
    linear_ring,
    polygon,
    multi_point,
    multi_line_string,
    multi_polygon,
    geometry_collection,
    empty,
)


@contextmanager
def assert_increases_refcount(obj):
    try:
        before = sys.getrefcount(obj)
    except AttributeError:  # happens on Pypy
        pytest.skip("sys.getrefcount is not available.")
    yield
    assert sys.getrefcount(obj) == before + 1


@contextmanager
def assert_decreases_refcount(obj):
    try:
        before = sys.getrefcount(obj)
    except AttributeError:  # happens on Pypy
        pytest.skip("sys.getrefcount is not available.")
    yield
    assert sys.getrefcount(obj) == before - 1


@contextmanager
def ignore_invalid(condition=True):
    if condition:
        with np.errstate(invalid="ignore"):
            yield
    else:
        yield
