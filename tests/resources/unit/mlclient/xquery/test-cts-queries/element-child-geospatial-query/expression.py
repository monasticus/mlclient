"""Serialization through the public CTS builder.

Native constructor: ``cts:element-child-geospatial-query``.
"""

from mlclient.xquery import cts


def run():
    return cts.element_child_geospatial_query("location", "point", cts.point(10, 20))
