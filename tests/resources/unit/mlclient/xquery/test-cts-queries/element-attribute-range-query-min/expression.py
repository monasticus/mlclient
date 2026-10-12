"""Serialization through the public CTS builder.

Native constructor: ``cts:element-attribute-range-query``.
"""

from mlclient.xquery import cts


def run():
    return cts.element_attribute_range_query("item", "amount", "!=", 3)
