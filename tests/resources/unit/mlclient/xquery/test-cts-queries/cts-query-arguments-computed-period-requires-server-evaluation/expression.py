"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

from mlclient.xquery import cts, fn


def run():
    query = cts.period_range_query("valid", "aln_before", period=fn.doc("/p.xml"))
    return query.serialize()
