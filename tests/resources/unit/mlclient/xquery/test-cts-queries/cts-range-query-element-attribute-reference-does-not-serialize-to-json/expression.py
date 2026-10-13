"""Public compilation and native serialization of RangeQuery."""

from mlclient.xquery import cts


def run():
    query = cts.range_query(
        cts.element_attribute_reference("item", "amount", options="type=int"),
        "=",
        2,
    )
    return query.to_json()
