"""Serialization through the public CTS builder.

Native constructor: ``cts:element-pair-geospatial-query``.
"""

from mlclient.xquery import cts


def run():
    return cts.element_pair_geospatial_query(
        "location",
        "lat",
        "lon",
        cts.point(10, 20),
    )
