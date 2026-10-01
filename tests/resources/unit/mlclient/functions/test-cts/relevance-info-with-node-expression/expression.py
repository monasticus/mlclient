from mlclient.functions.xqy import cts


def run():
    return cts.relevance_info(node=cts.search().index(1)).compile()
