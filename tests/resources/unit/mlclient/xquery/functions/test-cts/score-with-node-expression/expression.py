from mlclient.xquery import cts


def run():
    return cts.score(node=cts.search().pos(1)).compile()
