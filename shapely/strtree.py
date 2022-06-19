from typing import Any, Iterable, Union

import numpy as np

from . import lib
from .decorators import requires_geos, UnsupportedGEOSVersionError
from .enum import ParamEnum
from .geometry.base import BaseGeometry
from .predicates import is_empty, is_missing

__all__ = ["STRtree"]


class BinaryPredicate(ParamEnum):
    """The enumeration of GEOS binary predicates types"""

    intersects = 1
    within = 2
    contains = 3
    overlaps = 4
    crosses = 5
    touches = 6
    covers = 7
    covered_by = 8
    contains_properly = 9


class STRtree:
    """
    A query-only R-tree spatial index created using the
    Sort-Tile-Recursive (STR) [1]_ algorithm.

    For two-dimensional spatial data. The tree is constructed directly
    at initialization. The tree is immutable and query-only, meaning that
    once created nodes cannot be added or removed.

    All operations return indices of the input geometries.  These indices
    can be used to index into anything associated with the input geometries,
    including the input geometries themselves, or custom items stored in
    another object of the same length as the geometries.

    Any mixture of geometry types may be stored in the tree.

    Parameters
    ----------
    geoms : sequence
        A sequence of geometry objects.
    node_capacity : int, default 10
        The maximum number of child nodes per parent node in the tree.

    References
    ----------
    .. [1] Leutenegger, Scott T.; Edgington, Jeffrey M.; Lopez, Mario A.
       (February 1997). "STR: A Simple and Efficient Algorithm for
       R-Tree Packing".
       https://ia600900.us.archive.org/27/items/nasa_techdoc_19970016975/19970016975.pdf
    """

    def __init__(
        self,
        geoms: Iterable[BaseGeometry],
        node_capacity: int = 10,
    ):
        # Keep references to geoms
        self._geometries = np.asarray(geoms, dtype=np.object_)
        # prevent modification
        self._geometries.flags.writeable = False

        # initialize GEOS STRtree
        self._tree = lib.STRtree(self.geometries, node_capacity)

    def __len__(self):
        return self._tree.count

    def __reduce__(self):
        return (STRtree, (self.geometries,))

    @property
    def geometries(self):
        """
        Geometries stored in the tree in the order used to construct the tree.

        The order of this array corresponds to the tree indices returned by
        other STRtree methods.

        Do not attempt to modify items in the returned array.

        Returns
        -------
        ndarray of Geometry objects
        """
        return self._geometries

    def query(self, geometry, predicate=None, distance=None):
        """
        Return the integer indices of all combinations of each input geometry
        and tree geometries where the extent of each input geometry intersects
        the extent of a tree geometry.

        If the input geometry is a scalar, this returns an array of shape (n, ) with
        the indices of the matching tree geometries.  If the input geometry is an
        array_like, this returns an array with shape (2,n) where the subarrays
        correspond to the indices of the input geometries and indices of the
        tree geometries associated with each.  To generate an array of pairs of
        input geometry index and tree geometry index, simply transpose the
        result.

        If a predicate is provided, the tree geometries are further filtered to
        those that meet the predicate when comparing the input geometry to the
        tree geometry:
        predicate(geom, tree_geometry)

        The 'dwithin' predicate requires GEOS >= 3.10.

        Any input geometry that is None or empty will never match geometries
        in the tree.

        Parameters
        ----------
        geometry : Geometry or array_like
            Input geometries to query the tree and filter results using the
            optional predicate.
        predicate : {None, 'intersects', 'within', 'contains', 'overlaps', 'crosses',\
'touches', 'covers', 'covered_by', 'contains_properly', 'dwithin'}, optional
            The predicate to use for testing geometries from the tree
            that are within the input geometry's extent.
        distance : number or array_like, optional
            Distances around each input geometry within which to query the tree
            for the 'dwithin' predicate.  If array_like, shape must be
            broadcastable to shape of geometry.  Required if predicate='dwithin'.

        Returns
        -------
        ndarray with shape (n,) if geometry is a scalar
            Contains tree geometry indices.

        OR

        ndarray with shape (2, n) if geometry is an array_like
            The first subarray contains input geometry indices.
            The second subarray contains tree geometry indices.

        Examples
        --------
        >>> from shapely import box, Point
        >>> import numpy as np
        >>> points = [Point(0, 0), Point(1, 1), Point(2,2), Point(3, 3)]
        >>> tree = STRtree(points)

        Query the tree using a scalar geometry:

        >>> indices = tree.query(box(0, 0, 1, 1))
        >>> indices.tolist()
        [0, 1]

        Query using an array of geometries:

        >>> boxes = np.array([box(0, 0, 1, 1), box(2, 2, 3, 3)])
        >>> arr_indices = tree.query(boxes)
        >>> arr_indices.tolist()
        [[0, 0, 1, 1], [0, 1, 2, 3]]

        Or transpose to get all pairs of input and tree indices:

        >>> arr_indices.T.tolist()
        [[0, 0], [0, 1], [1, 2], [1, 3]]

        Retrieve the tree geometries by results of query:

        >>> tree.geometries.take(indices).tolist()
        [<shapely.Point POINT (0 0)>, <shapely.Point POINT (1 1)>]

        Retrieve all pairs of input and tree geometries:

        >>> np.array([boxes.take(arr_indices[0]),\
tree.geometries.take(arr_indices[1])]).T.tolist()
        [[<shapely.Polygon POLYGON ((1 0, 1 1, 0 1, 0 0, 1 0))>, <shapely.Point POINT (0 0)>],
         [<shapely.Polygon POLYGON ((1 0, 1 1, 0 1, 0 0, 1 0))>, <shapely.Point POINT (1 1)>],
         [<shapely.Polygon POLYGON ((3 2, 3 3, 2 3, 2 2, 3 2))>, <shapely.Point POINT (2 2)>],
         [<shapely.Polygon POLYGON ((3 2, 3 3, 2 3, 2 2, 3 2))>, <shapely.Point POINT (3 3)>]]

        Query using a predicate:

        >>> tree = STRtree([box(0, 0, 0.5, 0.5), box(0.5, 0.5, 1, 1), box(1, 1, 2, 2)])
        >>> tree.query(box(0, 0, 1, 1), predicate="contains").tolist()
        [0, 1]
        >>> tree.query(Point(0.75, 0.75), predicate="dwithin", distance=0.5).tolist()
        [0, 1, 2]

        >>> tree.query(boxes, predicate="contains").tolist()
        [[0, 0], [0, 1]]
        >>> tree.query(boxes, predicate="dwithin", distance=0.5).tolist()
        [[0, 0, 0, 1], [0, 1, 2, 2]]

        Retrieve custom items associated with tree geometries (records can
        be in whatever data structure so long as geometries and custom data
        can be extracted into arrays of the same length and order):

        >>> records = [
        ...     {"geometry": Point(0, 0), "value": "A"},
        ...     {"geometry": Point(2, 2), "value": "B"}
        ... ]
        >>> tree = STRtree([record["geometry"] for record in records])
        >>> items = np.array([record["value"] for record in records])
        >>> items.take(tree.query(box(0, 0, 1, 1))).tolist()
        ['A']


        Notes
        -----
        In the context of a spatial join, input geometries are the "left"
        geometries that determine the order of the results, and tree geometries
        are "right" geometries that are joined against the left geometries.
        This effectively performs an inner join, where only those combinations
        of geometries that can be joined based on overlapping extents or optional
        predicate are returned.
        """

        geometry = np.asarray(geometry)
        is_scalar = False
        if geometry.ndim == 0:
            geometry = np.expand_dims(geometry, 0)
            is_scalar = True

        if predicate is None:
            indices = self._tree.query(geometry, 0)
            return indices[1] if is_scalar else indices

        # Requires GEOS >= 3.10
        elif predicate == "dwithin":
            if lib.geos_version < (3, 10, 0):
                raise UnsupportedGEOSVersionError(
                    "dwithin predicate requires GEOS >= 3.10"
                )
            if distance is None:
                raise ValueError(
                    "distance parameter must be provided for dwithin predicate"
                )
            distance = np.asarray(distance, dtype="float64")
            if distance.ndim > 1:
                raise ValueError("Distance array should be one dimensional")

            try:
                distance = np.broadcast_to(distance, geometry.shape)
            except ValueError:
                raise ValueError("Could not broadcast distance to match geometry")

            indices = self._tree.dwithin(geometry, distance)
            return indices[1] if is_scalar else indices

        predicate = BinaryPredicate.get_value(predicate)
        indices = self._tree.query(geometry, predicate)
        return indices[1] if is_scalar else indices

    @requires_geos("3.6.0")
    def _nearest_idx(self, geometry, exclusive: bool = False):
        # TODO(shapely-2.0)
        if exclusive:
            raise NotImplementedError(
                "The `exclusive` keyword is not yet implemented for Shapely 2.0"
            )

        geometry_arr = np.asarray(geometry, dtype=object)
        # TODO those changes compared to _tree.nearest output should be pushed into C
        # _tree.nearest currently ignores missing values
        if is_missing(geometry_arr).any() or is_empty(geometry_arr).any():
            raise ValueError(
                "Cannot determine nearest geometry for empty geometry or "
                "missing value (None)."
            )
        # _tree.nearest returns ndarray with shape (2, 1) -> index in input
        # geometries and index into tree geometries
        indices = self._tree.nearest(np.atleast_1d(geometry_arr))[1]

        if geometry_arr.ndim == 0:
            return indices[0]
        else:
            return indices

    @requires_geos("3.6.0")
    def nearest(self, geom, exclusive: bool = False) -> Union[Any, None]:
        """
        Return the index of the nearest geometry in the tree for each input
        geometry.

        If there are multiple equidistant or intersected geometries in the tree,
        only a single result is returned for each input geometry, based on the
        order that tree geometries are visited; this order may be
        nondeterministic.

        If any input geometry is None or empty, an error is raised.

        Parameters
        ----------
        geom : Geometry or array_like
            Input geometries to query the tree.
        exclusive : bool, optional
            Whether to exclude the item corresponding to the given geom
            from results or not.  Default: False.

        Returns
        -------
        scalar or ndarray
            Indices of geometries in tree. Return value will have the same shape
            as the input.

            None is returned if this index is empty. This may change in
            version 2.0.

        See also
        --------
        nearest_all: returns all equidistant geometries and optional distances

        Examples
        --------
        >>> from shapely.geometry import Point
        >>> tree = STRtree([Point(i, i) for i in range(10)])

        Query the tree for nearest using a scalar geometry:

        >>> index = tree.nearest(Point(2.2, 2.2))
        >>> index
        2
        >>> tree.geometries.take(index)
        <shapely.Point POINT (2 2)>

        Query the tree for nearest using an array of geometries:

        >>> indices = tree.nearest([Point(2.2, 2.2), Point(4.4, 4.4)])
        >>> indices.tolist()
        [2, 4]
        >>> tree.geometries.take(indices).tolist()
        [<shapely.Point POINT (2 2)>, <shapely.Point POINT (4 4)>]


        Nearest only return one object if there are multiple equidistant results:

        >>> tree = STRtree ([Point(0, 0), Point(0, 0)])
        >>> tree.nearest(Point(0, 0))
        0
        """
        if self._tree.count == 0:
            return None

        return self._nearest_idx(geom, exclusive)

    @requires_geos("3.6.0")
    def nearest_all(self, geometry, max_distance=None, return_distance=False):
        """Returns the index of the nearest item(s) in the tree for each input
        geometry.

        If there are multiple equidistant or intersected geometries in tree, all
        are returned.  Tree indices are returned in the order they are visited
        for each input geometry and may not be in ascending index order; no meaningful
        order is implied.

        The max_distance used to search for nearest items in the tree may have a
        significant impact on performance by reducing the number of input geometries
        that are evaluated for nearest items in the tree.  Only those input geometries
        with at least one tree item within +/- max_distance beyond their envelope will
        be evaluated.

        The distance, if returned, will be 0 for any intersected geometries in the tree.

        Any geometry that is None or empty in the input geometries is omitted from
        the output.

        Parameters
        ----------
        geometry : Geometry or array_like
            Input geometries to query the tree.
        max_distance : float, optional
            Maximum distance within which to query for nearest items in tree.
            Must be greater than 0.
        return_distance : bool, default False
            If True, will return distances in addition to indices.

        Returns
        -------
        indices or tuple of (indices, distances)
            indices is an ndarray of shape (2,n) and distances (if present) an
            ndarray of shape (n).
            The first subarray of indices contains input geometry indices.
            The second subarray of indices contains tree geometry indices.

        See also
        --------
        nearest: returns singular nearest geometry for each input

        Examples
        --------
        >>> import shapely
        >>> tree = shapely.STRtree(shapely.points(np.arange(10), np.arange(10)))
        >>> tree.nearest_all(shapely.points(1,1)).tolist()  # doctest: +SKIP
        [[0], [1]]
        >>> tree.nearest_all( shapely.box(1,1,3,3)]).tolist()  # doctest: +SKIP
        [[0, 0, 0], [1, 2, 3]]
        >>> points = shapely.points(0.5,0.5)
        >>> index, distance = tree.nearest_all(points, return_distance=True)  # doctest: +SKIP
        >>> index.tolist()  # doctest: +SKIP
        [[0, 0], [0, 1]]
        >>> distance.round(4).tolist()  # doctest: +SKIP
        [0.7071, 0.7071]
        >>> tree.nearest_all(None).tolist()  # doctest: +SKIP
        [[], []]
        """

        geometry = np.asarray(geometry, dtype=object)
        if geometry.ndim == 0:
            geometry = np.expand_dims(geometry, 0)

        if max_distance is not None:
            if not np.isscalar(max_distance):
                raise ValueError("max_distance parameter only accepts scalar values")

            if max_distance <= 0:
                raise ValueError("max_distance must be greater than 0")

        # a distance of 0 means no max_distance is used
        max_distance = max_distance or 0

        if return_distance:
            return self._tree.nearest_all(geometry, max_distance)

        return self._tree.nearest_all(geometry, max_distance)[0]
