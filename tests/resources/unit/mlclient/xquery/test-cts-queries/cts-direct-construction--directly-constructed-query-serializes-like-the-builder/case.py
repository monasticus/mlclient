"""CTS query classes normalize their arguments exactly like the cts builder."""

from mlclient.xquery import ElementRangeQuery, cts

NS = "http://example.com/ns"


def run():
    assert (
        ElementRangeQuery("price", ">=", 10).to_json()
        == cts.element_range_query("price", ">=", 10).to_json()
    )
