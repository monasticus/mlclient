from mlclient.xquery import cts, xs


def run():
    return xs.double(cts.score(node=cts.search().pos(1))).compile()
