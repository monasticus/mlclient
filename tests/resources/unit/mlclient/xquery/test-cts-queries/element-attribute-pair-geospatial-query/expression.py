"""Serialization through the public CTS builder.

Native constructor: ``cts:element-attribute-pair-geospatial-query``.
"""

from mlclient.xquery import cts


def run():
    return cts.element_attribute_pair_geospatial_query(
        "item",
        "lat",
        "lon",
        cts.point(10, 20),
        weight=3,
    )
