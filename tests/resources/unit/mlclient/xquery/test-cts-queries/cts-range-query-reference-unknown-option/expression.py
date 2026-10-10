"""Public compilation and native serialization of RangeQuery."""

from mlclient.xquery import cts


def run():
    return cts.range_query(
        cts.element_reference("price", options="unknown"),
        "=",
        2,
    ).serialize()
