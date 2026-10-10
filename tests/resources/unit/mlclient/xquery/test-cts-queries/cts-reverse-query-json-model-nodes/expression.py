"""Public compilation and native serialization of ReverseQuery."""

from mlclient.xquery import FunctionCall, cts


def run():
    return cts.reverse_query(
        FunctionCall("xdmp:unquote", ('{"label":"blue","count":2}',)),
    )
