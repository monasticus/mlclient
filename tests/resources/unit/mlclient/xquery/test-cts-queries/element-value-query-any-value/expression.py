"""Native ``cts:element-value-query`` serialization through the public CTS builder."""

from mlclient.xquery import cts


def run():
    return cts.element_value_query("title")
