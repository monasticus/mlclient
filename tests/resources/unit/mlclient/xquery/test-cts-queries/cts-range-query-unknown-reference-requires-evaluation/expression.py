"""Public compilation and native serialization of RangeQuery."""

from mlclient.xquery import cts, fn


def run():
    return cts.range_query(fn.doc("/reference.xml"), "=", 2).serialize()
