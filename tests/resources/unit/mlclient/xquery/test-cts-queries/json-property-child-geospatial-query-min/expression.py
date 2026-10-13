"""Serialization through the public CTS builder.

Native constructor: ``cts:json-property-child-geospatial-query``.
"""

from mlclient.xquery import cts


def run():
    return cts.json_property_child_geospatial_query(
        "location",
        "point",
        cts.point(10, 20),
    )
