"""Serialization through the public CTS builder.

Native constructor: ``cts:element-attribute-value-query``.
"""

from mlclient.xquery import cts


def run():
    return cts.element_attribute_value_query(
        "item",
        "status",
        "ok",
        options="exact",
        weight=0.5,
    )
