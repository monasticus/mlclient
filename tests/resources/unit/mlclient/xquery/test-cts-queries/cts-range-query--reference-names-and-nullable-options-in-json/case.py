"""Public compilation and native serialization of RangeQuery."""

from tests.utils.resources import read_query_expectation
from mlclient.xquery import cts


def run():
    query = cts.range_query(
        [
            cts.field_reference("price", options=["type=int", "non-nullable"]),
            cts.json_property_reference("price", options="type=int"),
            cts.path_reference("/report/price", options="type=int"),
            cts.uri_reference(),
            cts.collection_reference(),
            cts.iri_reference(),
        ],
        "=",
        "blue",
    )
    assert query.to_json() == read_query_expectation(__file__, "expected-1.json")
