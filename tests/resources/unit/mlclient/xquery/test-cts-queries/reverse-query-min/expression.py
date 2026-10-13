"""Public compilation and native serialization of ReverseQuery."""

from mlclient.xquery import FunctionCall, cts


def run():
    source = '<report xmlns:r="https://example.com/reports" kind="r:blue">blue</report>'
    return cts.reverse_query(FunctionCall("xdmp:unquote", (source,)))
