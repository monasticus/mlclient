"""Public compilation and native serialization of SimilarQuery."""

from mlclient.xquery import FunctionCall, cts


def run():
    query = cts.similar_query(
        None,
        options=FunctionCall("xdmp:unquote", ('{"maxTerms":20}',)),
    )
    return query.serialize()
