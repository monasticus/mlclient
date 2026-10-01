from mlclient.functions.xqy import cts, xs


def run():
    return xs.double(cts.score(node=cts.search().index(1))).compile()
