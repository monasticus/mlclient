"""Serialization through the public CTS builder.

Native constructor: ``cts:element-attribute-word-query``.
"""

from mlclient.xquery import cts


def run():
    return cts.element_attribute_word_query("item", "status", "ok")
