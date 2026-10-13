"""Public compilation and native serialization of RangeQuery."""

from mlclient.xquery import cts


def run():
    query = cts.range_query(
        cts.path_reference(
            "/r:report/r:price",
            options="type=int",
            namespaces={"r": "https://example.com/reports"},
        ),
        "=",
        2,
    )
    return query.serialize()
