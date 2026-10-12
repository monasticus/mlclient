"""Serialization through the public CTS builder.

Native constructor: ``cts:element-geospatial-query``.
"""

from mlclient.xquery import cts


def run():
    return cts.element_geospatial_query(
        "origin",
        cts.point(10.5, -20.25),
        options="coordinate-system=wgs84",
        weight=2,
    )
