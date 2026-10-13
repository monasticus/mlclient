"""Public compilation and native serialization of RangeQuery."""

from mlclient.xquery import FunctionCall, cts


def run():
    return cts.range_query(
        FunctionCall("cts:reference-parse", ("reference",)),
        "=",
        2,
    ).serialize()
