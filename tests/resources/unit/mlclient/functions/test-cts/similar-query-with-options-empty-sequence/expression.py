from mlclient.functions.xqy import cts


def run():
    return cts.similar_query(cts.search().index(1), options=None).compile()
