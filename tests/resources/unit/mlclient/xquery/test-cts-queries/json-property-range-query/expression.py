"""Serialization through the public CTS builder.

Native constructor: ``cts:json-property-range-query``.
"""

from mlclient.xquery import cts


def run():
    return cts.json_property_range_query("price", ">", 10)
