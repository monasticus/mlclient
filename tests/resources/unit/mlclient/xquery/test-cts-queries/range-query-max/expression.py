"""Public compilation and native serialization of RangeQuery."""

from mlclient.xquery import cts


def run():
    return cts.range_query(
        cts.element_reference("price", options=["type=int", "unchecked"]),
        ">=",
        [2, 3],
        options="cached",
        weight=2,
    )
