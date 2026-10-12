"""Serialization through the public CTS builder.

Native constructor: ``cts:json-property-pair-geospatial-query``.
"""

from mlclient.xquery import cts


def run():
    return cts.json_property_pair_geospatial_query(
        "location",
        "lat",
        "lon",
        cts.point(10, 20),
    )
