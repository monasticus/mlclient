"""Public compilation and native serialization of SimilarQuery."""

from mlclient.xquery import cts, fn


def run():
    query = cts.similar_query(None, options=fn.doc("/options.xml"))
    return query.serialize()
