"""Public compilation and native serialization of RangeQuery."""

from mlclient.xquery import cts


def run():
    reference = cts.element_reference("price", options="type=int").pos(1)
    return cts.range_query(reference, "=", 2).serialize()
