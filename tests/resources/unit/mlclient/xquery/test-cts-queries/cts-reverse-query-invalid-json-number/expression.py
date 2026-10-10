"""Public compilation and native serialization of ReverseQuery."""

from mlclient.xquery import FunctionCall, cts


def run():
    query = cts.reverse_query(FunctionCall("xdmp:unquote", ('{"count":NaN}',)))
    return query.serialize()
