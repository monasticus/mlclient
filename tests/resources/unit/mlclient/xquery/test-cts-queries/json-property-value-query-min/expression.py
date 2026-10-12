"""Serialization through the public CTS builder.

Native constructor: ``cts:json-property-value-query``.
"""

from mlclient.xquery import cts


def run():
    return cts.json_property_value_query("label", "gamma")
