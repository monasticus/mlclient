"""Native ``cts:field-value-query`` serialization through the public CTS builder."""

from mlclient.xquery import cts


def run():
    return cts.field_value_query("price", ["1", "2"], weight=3)
