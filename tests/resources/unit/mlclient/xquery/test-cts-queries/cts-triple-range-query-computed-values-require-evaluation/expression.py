"""Public compilation and native serialization of TripleRangeQuery."""

from mlclient.xquery import cts, fn


def run():
    query = cts.triple_range_query(None, None, fn.doc("/value.xml"))
    return query.serialize()
