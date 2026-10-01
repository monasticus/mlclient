from mlclient.functions.xqy import cts


def run():
    return cts.score(node=cts.search().index(1)).compile()
