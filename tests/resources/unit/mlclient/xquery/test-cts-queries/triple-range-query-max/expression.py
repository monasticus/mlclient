"""Public compilation and native serialization of TripleRangeQuery."""

from mlclient.xquery import FunctionCall, cts


def run():
    return cts.triple_range_query(
        FunctionCall("sem:iri", ("https://example.com/r",)),
        FunctionCall("sem:iri", ("https://example.com/p",)),
        [2, True, "blue"],
        operator=">",
        options="cached",
        weight=2,
    )
