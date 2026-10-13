"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

from mlclient.xquery import cts, fn


def run():
    return cts.element_range_query("price", ">", fn.count(fn.doc())).serialize()
