"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

from mlclient.xquery import FunctionCall, cts


def run():
    query = cts.reverse_query(FunctionCall("xdmp:unquote", ("<a><b></a>",)))
    return query.to_xml()
