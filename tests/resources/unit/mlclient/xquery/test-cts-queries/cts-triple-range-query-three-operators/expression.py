"""Public compilation and native serialization of TripleRangeQuery."""

from mlclient.xquery import cts


def run():
    return cts.triple_range_query("blue", "label", 2, operator=["!=", "=", ">"])
