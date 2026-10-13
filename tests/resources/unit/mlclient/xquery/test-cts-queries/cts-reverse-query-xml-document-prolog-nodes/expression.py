"""Public compilation and native serialization of ReverseQuery."""

from mlclient.xquery import FunctionCall, cts


def run():
    source = '<?xml version="1.0"?><?label blue?><!--report--><report>blue</report>'
    return cts.reverse_query(FunctionCall("xdmp:unquote", (source,)))
