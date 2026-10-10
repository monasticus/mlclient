from mlclient.xquery import cts


def run():
    return cts.relevance_info(node=cts.search().pos(1)).compile()
