"""Public compilation and native serialization of TripleRangeQuery."""

from mlclient.xquery import cts


def run():
    query = cts.triple_range_query(None, None, 2, operator=["=", "="])
    return query.serialize()
