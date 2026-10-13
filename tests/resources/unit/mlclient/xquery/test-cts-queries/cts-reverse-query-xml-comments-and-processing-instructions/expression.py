"""Public compilation and native serialization of ReverseQuery."""

from mlclient.xquery import FunctionCall, cts


def run():
    source = "<report><!--label--><?label blue?><label>blue</label></report>"
    return cts.reverse_query(FunctionCall("xdmp:unquote", (source,)))
