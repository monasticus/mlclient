"""Public compilation and native serialization of SimilarQuery."""

from mlclient.xquery import FunctionCall, cts


def run():
    options = '<options xmlns="cts:distinctive-terms"><unknown>true</unknown></options>'
    query = cts.similar_query(
        None,
        options=FunctionCall("xdmp:unquote", (options,)).xpath("*"),
    )
    return query.serialize()
